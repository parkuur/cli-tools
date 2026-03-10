from __future__ import annotations

import argparse
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

from cli_layer.install import manifest, profile
from core_lib.common.platform import get_data_dir

TOOL_NAME = "teleport"
EXIT_USAGE = 1
EXIT_UNSUPPORTED_SHELL = 2
EXIT_PERMISSION = 3
EXIT_FAILURE = 4


def default_profiles_for_shell(shell: str) -> list[Path]:
    home = Path.home()
    if shell == "bash":
        return [home / ".bashrc"]
    if shell == "zsh":
        return [home / ".zshrc"]
    if shell == "fish":
        return [home / ".config" / "fish" / "config.fish"]
    if shell in ("powershell", "pwsh"):
        return [home / "Documents" / "PowerShell" / "Microsoft.PowerShell_profile.ps1"]
    if shell in ("cmd", "bat"):
        return [home / "init.bat"]
    return [home / ".profile"]


def marker_id_for(tool: str, filename: str) -> str:
    return f"{tool}#{filename}"


def shell_to_ext(shell: str) -> str:
    if shell.startswith("power") or shell == "pwsh":
        return "ps1"
    if shell in ("bash", "zsh"):
        return "bash"
    if shell == "fish":
        return "fish"
    if shell in ("cmd", "bat"):
        return "bat"
    raise ValueError(f"unsupported shell {shell}")


def _resolve_snippet(shell: str) -> tuple[Path, str, str, str]:
    snippets_dir = Path(__file__).parent.parent / "shell_snippets"
    ext = shell_to_ext(shell)
    snippet_path = snippets_dir / f"tp.{ext}"
    filename = snippet_path.name
    marker_id = marker_id_for(TOOL_NAME, filename)
    return snippet_path, filename, marker_id, ext


def _emit_summary(counts: dict[str, int]) -> None:
    print(
        (
            "[summary] "
            f"install={counts['install']} "
            f"update={counts['update']} "
            f"noop={counts['noop']} "
            f"skip={counts['skip']} "
            f"errors={counts['errors']}"
        ),
        file=sys.stderr,
    )


def _map_error(exc: BaseException, target: Path) -> int:
    if isinstance(exc, PermissionError):
        print(f"Permission failure writing {target}", file=sys.stderr)
        return EXIT_PERMISSION
    print(f"Install failed: {exc}", file=sys.stderr)
    return EXIT_FAILURE


def install(args: argparse.Namespace) -> int:
    shell = args.shell
    supported = ("bash", "zsh", "fish", "powershell", "pwsh", "cmd", "bat")
    if shell not in supported:
        print(f"Unsupported shell: {shell}", file=sys.stderr)
        return EXIT_UNSUPPORTED_SHELL
    profiles = args.profiles.split(",") if args.profiles else None
    targets = [Path(p).expanduser() for p in (profiles or [])] or default_profiles_for_shell(shell)

    data_dir = get_data_dir()
    manifest_path = data_dir / "install_manifest.json"
    snippet_path, filename, marker_id, _ = _resolve_snippet(shell)
    if not snippet_path.exists():
        print(f"Snippet not found: {snippet_path}", file=sys.stderr)
        return EXIT_FAILURE

    snippet = snippet_path.read_text(encoding="utf-8")
    # Resolve the tp-cli executable from the current Python environment and bake
    # its absolute path into the snippet so the shell function works without any
    # active virtualenv or uv on PATH.
    _exe_name = "tp-cli.exe" if sys.platform.startswith("win") else "tp-cli"
    _exe = Path(sys.executable).parent / _exe_name
    if not _exe.exists():
        _found = shutil.which("tp-cli")
        if _found:
            _exe = Path(_found)
    snippet = snippet.replace("{{TP_CLI}}", str(_exe))
    checksum = manifest.compute_checksum(snippet_path)
    source_path = str(Path("src") / "cli_layer" / "shell_snippets" / filename)
    counts: dict[str, int] = {"install": 0, "update": 0, "noop": 0, "skip": 0, "errors": 0}

    for prof in targets:
        try:
            if args.dry_run:
                print(f"[plan] would install {marker_id} into {prof}", file=sys.stderr)
                counts["skip"] += 1
                continue

            existing = manifest.get_marker(manifest_path, marker_id)
            # Respect disabled markers before creating profile files
            if existing and existing.get("enabled") is False:
                print(f"[skip] {marker_id} disabled in manifest", file=sys.stderr)
                counts["skip"] += 1
                continue

            # ensure file exists (create lazily only when we will modify)
            if not prof.exists():
                prof.parent.mkdir(parents=True, exist_ok=True)
                prof.write_text("", encoding="utf-8")

            current_text = prof.read_text(encoding="utf-8")
            current_block = profile.get_marker_block(
                current_text,
                marker_id,
                comment=profile.COMMENT_SYNTAX.get(shell, "#"),
            )
            expected_block = profile.build_marker_block(
                marker_id,
                filename,
                snippet,
                comment=profile.COMMENT_SYNTAX.get(shell, "#"),
            )

            cond_checksum = existing and existing.get("checksum") == checksum
            if cond_checksum and current_block == expected_block:
                print(f"[noop] {prof}", file=sys.stderr)
                counts["noop"] += 1
                continue

            # if marker exists but checksum differs, remove then insert
            try:
                profile.remove_marker_from_profile(prof, marker_id, shell=shell)
            except (OSError, ValueError):
                pass

            backup = profile.insert_marker_into_profile(
                prof,
                marker_id,
                filename,
                snippet,
                shell=shell,
                tool_name=TOOL_NAME,
            )

            if existing is None:
                manifest.add_marker(
                    manifest_path,
                    marker_id,
                    source_path,
                    [str(prof)],
                    checksum,
                    enabled=True,
                )
                # append backup info
                manifest.update_marker(
                    manifest_path,
                    marker_id,
                    backups=[
                        {
                            "profile": str(prof),
                            "backup_path": str(backup),
                            "timestamp": datetime.now(UTC).isoformat(),
                        }
                    ],
                )
            else:
                # update existing entry
                updates = {
                    "checksum": checksum,
                    "profiles": list(set(existing.get("profiles", []) + [str(prof)])),
                }
                # append backup to backups list
                bks = existing.get("backups", []) or []
                bks.append(
                    {
                        "profile": str(prof),
                        "backup_path": str(backup),
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                )
                updates["backups"] = bks
                manifest.update_marker(manifest_path, marker_id, **updates)

            if existing is None or current_block is None:
                print(f"[install] {prof}", file=sys.stderr)
                counts["install"] += 1
            else:
                print(f"[update] {prof}", file=sys.stderr)
                counts["update"] += 1
        except PermissionError:
            counts["errors"] += 1
            _emit_summary(counts)
            return EXIT_PERMISSION
        except (OSError, ValueError, KeyError) as exc:
            counts["errors"] += 1
            _emit_summary(counts)
            return _map_error(exc, prof)

    _emit_summary(counts)
    return 0


def uninstall(args: argparse.Namespace) -> int:
    shell = args.shell
    supported = ("bash", "zsh", "fish", "powershell", "pwsh", "cmd", "bat")
    if shell not in supported:
        print(f"Unsupported shell: {shell}", file=sys.stderr)
        return EXIT_UNSUPPORTED_SHELL
    profiles = args.profiles.split(",") if args.profiles else None
    targets = [Path(p).expanduser() for p in (profiles or [])] or default_profiles_for_shell(shell)
    data_dir = get_data_dir()
    manifest_path = data_dir / "install_manifest.json"
    _, _, marker_tp, _ = _resolve_snippet(shell)
    counts: dict[str, int] = {"install": 0, "update": 0, "noop": 0, "skip": 0, "errors": 0}

    for prof in targets:
        try:
            removed = profile.remove_marker_from_profile(prof, marker_tp, shell=shell)
            if removed:
                # attempt to restore latest backup recorded in manifest
                meta = manifest.get_marker(manifest_path, marker_tp)
                if meta:
                    backups = meta.get("backups", []) or []
                    if backups:
                        latest = backups[-1]
                        backup_path = Path(latest.get("backup_path"))
                        try:
                            profile.restore_backup_to_profile(backup_path, prof)
                        except (FileNotFoundError, OSError):
                            # if restore fails, continue but keep note
                            print(f"[warn] failed to restore backup {backup_path}", file=sys.stderr)
                if meta:
                    remaining_profiles = [
                        p for p in (meta.get("profiles", []) or []) if p != str(prof)
                    ]
                    if remaining_profiles:
                        manifest.update_marker(
                            manifest_path,
                            marker_tp,
                            profiles=remaining_profiles,
                        )
                    else:
                        manifest.remove_marker(manifest_path, marker_tp)
                print(f"[uninstall] removed from {prof}", file=sys.stderr)
                counts["update"] += 1
            else:
                print(f"[noop] no marker in {prof}", file=sys.stderr)
                counts["noop"] += 1
        except PermissionError:
            counts["errors"] += 1
            _emit_summary(counts)
            print(f"Permission failure writing {prof}", file=sys.stderr)
            return EXIT_PERMISSION
        except (OSError, ValueError, KeyError) as exc:
            counts["errors"] += 1
            _emit_summary(counts)
            print(f"Uninstall failed: {exc}", file=sys.stderr)
            return EXIT_FAILURE

    _emit_summary(counts)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="install-shell-snippet")
    p.add_argument("--uninstall", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--shell", default="bash")
    p.add_argument("--profiles", default="")
    p.add_argument("--no-tp", action="store_true")
    p.add_argument("--tp", action="store_true")
    args, unknown = p.parse_known_args(argv)
    setattr(args, "unknown_args", unknown)
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    unknown_args = getattr(args, "unknown_args", [])
    if unknown_args:
        for flag in unknown_args:
            if flag.startswith("--no-") or flag.startswith("--"):
                print(f"Unknown flag: {flag}", file=sys.stderr)
                return EXIT_USAGE
            print(f"Unknown argument: {flag}", file=sys.stderr)
            return EXIT_USAGE

    data_dir = get_data_dir()
    manifest_path = data_dir / "install_manifest.json"
    try:
        _, _, marker, _ = _resolve_snippet(args.shell)
    except ValueError:
        marker = marker_id_for(TOOL_NAME, "tp.bash")

    if args.no_tp:
        if args.dry_run:
            print(f"[plan] would disable {marker}", file=sys.stderr)
            return 0
        # record disabled state in manifest for the teleport marker
        try:
            manifest.set_marker_enabled(manifest_path, marker, False)
        except PermissionError:
            return EXIT_PERMISSION
        except OSError:
            return EXIT_FAILURE
        print("[skip] tp disabled by flag", file=sys.stderr)
        return 0
    if args.tp:
        if args.dry_run:
            print(f"[plan] would enable {marker}", file=sys.stderr)
            return 0
        try:
            manifest.set_marker_enabled(manifest_path, marker, True)
        except PermissionError:
            return EXIT_PERMISSION
        except OSError:
            return EXIT_FAILURE
        print("[enable] tp enabled by flag", file=sys.stderr)
        return 0
    if args.uninstall:
        return uninstall(args)
    return install(args)


if __name__ == "__main__":
    sys.exit(main())
