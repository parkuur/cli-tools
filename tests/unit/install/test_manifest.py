# pyright: reportMissingTypeStubs=false

import json
import os
from pathlib import Path


def test_add_marker_to_manifest(tmp_path: Path) -> None:
    from cli_layer.install import manifest

    p = tmp_path / "install_manifest.json"
    manifest.add_marker(
        p,
        "teleport#tp.bash",
        "src/cli_layer/shell_snippets/tp.bash",
        ["/tmp/.bashrc"],
        "abc123",
        enabled=True,
    )
    got = manifest.get_marker(p, "teleport#tp.bash")
    assert got is not None
    assert got["source"] == "src/cli_layer/shell_snippets/tp.bash"
    assert got["profiles"] == ["/tmp/.bashrc"]
    assert got["checksum"] == "abc123"
    assert got["enabled"] is True


def test_update_marker_checksum(tmp_path: Path) -> None:
    from cli_layer.install import manifest

    p = tmp_path / "install_manifest.json"
    marker = "teleport#tp.bash"
    manifest.add_marker(
        p,
        marker,
        "src/cli_layer/shell_snippets/tp.bash",
        ["/tmp/.bashrc"],
        "abc123",
    )
    manifest.update_marker(p, marker, checksum="def456")
    got = manifest.get_marker(p, marker)
    assert got is not None
    assert got["checksum"] == "def456"


def test_remove_marker_from_manifest(tmp_path: Path) -> None:
    from cli_layer.install import manifest

    p = tmp_path / "install_manifest.json"
    manifest.add_marker(p, "teleport#tp.bash", "src/cli_layer/shell_snippets/tp.bash", [], "a")
    manifest.add_marker(p, "bookmarks#bm.bash", "src/cli_layer/shell_snippets/bm.bash", [], "b")
    manifest.remove_marker(p, "teleport#tp.bash")
    assert manifest.get_marker(p, "teleport#tp.bash") is None
    assert manifest.get_marker(p, "bookmarks#bm.bash") is not None


def test_get_marker_returns_metadata(tmp_path: Path) -> None:
    from cli_layer.install import manifest

    p = tmp_path / "install_manifest.json"
    marker = "teleport#tp.bash"
    manifest.add_marker(p, marker, "src/cli_layer/shell_snippets/tp.bash", ["/tmp/.bashrc"], "abc")
    got = manifest.get_marker(p, marker)
    assert got is not None
    assert "source" in got
    assert "profiles" in got
    assert "checksum" in got
    assert "enabled" in got
    assert "installed_at" in got


def test_get_nonexistent_marker_returns_none(tmp_path: Path) -> None:
    from cli_layer.install import manifest

    p = tmp_path / "install_manifest.json"
    assert manifest.get_marker(p, "missing#marker") is None


def test_compute_checksum_sha256(tmp_path: Path) -> None:
    from cli_layer.install import manifest

    f = tmp_path / "snippet.sh"
    f.write_text("echo hi\n", encoding="utf-8")
    digest = manifest.compute_checksum(f)
    assert len(digest) == 64
    assert all(c in "0123456789abcdef" for c in digest)


def test_compute_checksum_identical_for_same_content(tmp_path: Path) -> None:
    from cli_layer.install import manifest

    a = tmp_path / "a.sh"
    b = tmp_path / "b.sh"
    content = "same\ncontent\n"
    a.write_text(content, encoding="utf-8")
    b.write_text(content, encoding="utf-8")
    assert manifest.compute_checksum(a) == manifest.compute_checksum(b)


def test_manifest_handles_multiple_tools(tmp_path: Path) -> None:
    from cli_layer.install import manifest

    p = tmp_path / "install_manifest.json"
    manifest.add_marker(p, "teleport#tp.bash", "src/cli_layer/shell_snippets/tp.bash", [], "a")
    manifest.add_marker(p, "bookmarks#bm.bash", "src/cli_layer/shell_snippets/bm.bash", [], "b")
    loaded = manifest.read_manifest(p)
    installed = loaded.get("installed", {})
    assert "teleport#tp.bash" in installed
    assert "bookmarks#bm.bash" in installed


def test_enabled_flag_defaults_to_true(tmp_path: Path) -> None:
    from cli_layer.install import manifest

    p = tmp_path / "install_manifest.json"
    marker = "teleport#tp.bash"
    manifest.add_marker(p, marker, "src/cli_layer/shell_snippets/tp.bash", [], "x")
    got = manifest.get_marker(p, marker)
    assert got is not None
    assert got["enabled"] is True


def test_disabled_marker_preserved_in_manifest(tmp_path: Path) -> None:
    from cli_layer.install import manifest

    p = tmp_path / "install_manifest.json"
    marker = "teleport#tp.bash"
    manifest.add_marker(p, marker, "src/cli_layer/shell_snippets/tp.bash", [], "x", enabled=False)
    got = manifest.get_marker(p, marker)
    assert got is not None
    assert got["enabled"] is False


def test_manifest_tolerates_missing_fields(tmp_path: Path) -> None:
    from cli_layer.install import manifest

    p = tmp_path / "install_manifest.json"
    broken = {
        "installed": {
            "teleport#tp.bash": {
                "source": "src/cli_layer/shell_snippets/tp.bash",
                "profiles": ["~/.bashrc"],
                "checksum": "abc",
            }
        }
    }
    p.write_text(json.dumps(broken), encoding="utf-8")
    got = manifest.get_marker(p, "teleport#tp.bash")
    assert got is not None
    assert got["enabled"] is True
    assert got["backups"] == []


def test_create_manifest_with_restrictive_permissions(tmp_path: Path) -> None:
    from cli_layer.install import manifest

    p = tmp_path / "install_manifest.json"
    manifest.create_manifest(p)
    assert p.exists()
    assert manifest.read_manifest(p) == {"installed": {}}

    # Permissions check only on POSIX-like systems
    if os.name != "nt":
        mode = p.stat().st_mode & 0o777
        assert mode == 0o600


def test_read_empty_manifest(tmp_path: Path) -> None:
    from cli_layer.install import manifest

    p = tmp_path / "install_manifest.json"
    p.write_text(json.dumps({"installed": {}}), encoding="utf-8")
    assert manifest.read_manifest(p) == {"installed": {}}


def test_read_nonexistent_manifest_returns_default(tmp_path: Path) -> None:
    from cli_layer.install import manifest

    p = tmp_path / "does_not_exist.json"
    assert not p.exists()
    assert manifest.read_manifest(p) == {"installed": {}}


def test_write_manifest_atomically(tmp_path: Path) -> None:
    from cli_layer.install import manifest

    p = tmp_path / "install_manifest.json"
    data = {"installed": {"teleport#tp.bash": {"source": "src/cli_layer/shell_snippets/tp.bash"}}}
    manifest.write_manifest(p, data)
    assert p.exists()

    # No leftover temp files matching the temp naming pattern
    tmp_files = list(tmp_path.glob("install_manifest.json.*.tmp"))
    assert not tmp_files

    read = json.loads(p.read_text(encoding="utf-8"))
    assert read == data
