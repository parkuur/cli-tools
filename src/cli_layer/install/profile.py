from __future__ import annotations

import os
import re
import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from re import Pattern

from core_lib.common.platform import get_data_dir

COMMENT_SYNTAX = {
    "bash": "#",
    "zsh": "#",
    "fish": "#",
    "powershell": "#",
    "cmd": "REM",
}


def _marker_regex(marker_id: str, comment: str) -> tuple[Pattern[str], Pattern[str]]:
    # header uses marker id, footer uses filename part after '#'
    # Build header pattern in parts to avoid very long literal lines.
    hdr_pat = r"^" + re.escape(comment) + r"\s*>>>\s*.*\(id:\s*" + re.escape(marker_id) + r"\).*$"
    header = re.compile(hdr_pat, re.MULTILINE)
    # derive filename from marker id (teleport#tp.bash -> tp.bash)
    if "#" in marker_id:
        filename = marker_id.split("#", 1)[1]
    else:
        filename = Path(marker_id).name
    footer = re.compile(rf"^{re.escape(comment)}\s*<<<\s*.*{re.escape(filename)}.*$", re.MULTILINE)
    return header, footer


def detect_marker(text: str, marker_id: str, comment: str = "#") -> tuple[int, int] | None:
    """Return (start_idx, end_idx) of the marker block in text, or None.

    start_idx is index of header line start, end_idx is end of footer line.
    """
    header_re, footer_re = _marker_regex(marker_id, comment)
    header_match = header_re.search(text)
    if not header_match:
        return None
    footer_match = footer_re.search(text, header_match.end())
    if not footer_match:
        return None
    return header_match.start(), footer_match.end()


def build_marker_block(marker_id: str, filename: str, snippet: str, comment: str = "#") -> str:
    header = f"{comment} >>> teleport snippet: {filename} (id: {marker_id})\n"
    footer = f"{comment} <<< teleport snippet: {filename}\n"
    return header + snippet.rstrip("\n") + "\n" + footer


def get_marker_block(text: str, marker_id: str, comment: str = "#") -> str | None:
    """Return the full marker block text for marker_id or None if missing."""
    rng = detect_marker(text, marker_id, comment)
    if rng is None:
        return None
    start, end = rng
    if end < len(text) and text[end : end + 1] == "\n":
        end += 1
    return text[start:end]


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=f"{path.name}.", suffix=".tmp")
    tmp_path = Path(tmp)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(str(tmp_path), str(path))
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass


def _prune_backups(backups_dir: Path, keep_last: int = 5) -> None:
    if keep_last <= 0 or not backups_dir.exists():
        return
    backups = sorted(backups_dir.glob("*.bak"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in backups[keep_last:]:
        try:
            old.unlink()
        except OSError:
            pass


def create_backup(profile_path: Path, tool_name: str) -> Path:
    data_dir = get_data_dir()
    backups_dir = data_dir / "backups" / tool_name
    backups_dir.mkdir(parents=True, exist_ok=True)
    # filename safe
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    safe_name = profile_path.name.replace("/", "_")
    backup_name = f"{safe_name}.{timestamp}.bak"
    backup_path = backups_dir / backup_name
    if profile_path.exists():
        shutil.copy2(profile_path, backup_path)
    else:
        backup_path.write_text("", encoding="utf-8")
    try:
        backup_path.chmod(0o600)
    except OSError:
        pass
    _prune_backups(backups_dir, keep_last=5)
    return backup_path


def insert_marker_into_profile(
    profile_path: Path,
    marker_id: str,
    filename: str,
    snippet: str,
    shell: str = "bash",
    tool_name: str = "teleport",
    create_if_missing: bool = True,
) -> Path:
    """Insert marker block into profile file and create a backup. Returns backup path.

    If marker already present, raises ValueError.
    """
    comment = COMMENT_SYNTAX.get(shell, "#")
    content = ""
    if profile_path.exists():
        content = profile_path.read_text(encoding="utf-8")
    else:
        if not create_if_missing:
            raise FileNotFoundError(profile_path)
        content = ""

    if detect_marker(content, marker_id, comment) is not None:
        raise ValueError("marker exists")

    # Create backup
    backup = create_backup(profile_path, tool_name)

    # Append marker to end with a separating newline if needed
    if content and not content.endswith("\n"):
        content = content + "\n"
    content = content + build_marker_block(marker_id, filename, snippet, comment)

    _atomic_write(profile_path, content)
    return backup


def remove_marker_from_profile(profile_path: Path, marker_id: str, shell: str = "bash") -> bool:
    comment = COMMENT_SYNTAX.get(shell, "#")
    if not profile_path.exists():
        return False
    text = profile_path.read_text(encoding="utf-8")
    rng = detect_marker(text, marker_id, comment)
    if not rng:
        return False
    start, end = rng
    new_text = text[:start] + text[end:]
    _atomic_write(profile_path, new_text)
    return True


def restore_backup_to_profile(backup_path: Path, profile_path: Path) -> None:
    """Restore the backup file to the given profile path atomically."""
    if not backup_path.exists():
        raise FileNotFoundError(backup_path)
    # Use atomic write by copying to temp and replacing
    _atomic_write(profile_path, backup_path.read_text(encoding="utf-8"))
