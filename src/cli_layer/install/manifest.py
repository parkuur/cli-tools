from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def default_manifest() -> dict[str, Any]:
    return {"installed": {}}


def create_manifest(path: Path) -> None:
    """Create a manifest file at `path` with restrictive permissions (0o600).

    The write is atomic: content is written to a temporary file in the same
    directory and then renamed into place.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    data = default_manifest()
    write_manifest(path, data)


def read_manifest(path: Path) -> dict[str, Any]:
    """Read and return manifest JSON as a dict.

    If the file does not exist or is invalid, return the default manifest
    structure instead of raising.
    """
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return default_manifest()
    except (json.JSONDecodeError, OSError):
        # Corrupted or unreadable manifest: return default to allow recovery.
        return default_manifest()


def write_manifest(path: Path, data: dict[str, Any]) -> None:
    """Write manifest atomically to `path` and set restrictive permissions.

    Uses a temporary file in the same directory and then atomically replaces
    the target path. On POSIX the final file mode will be 0o600. Errors
    during chmod are ignored to preserve cross-platform compatibility.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    dirpath = path.parent

    # Create a temp file in the same directory for atomic replace semantics.
    fd, tmp = tempfile.mkstemp(dir=str(dirpath), prefix=f"{path.name}.", suffix=".tmp")
    tmp_path = Path(tmp)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
            fh.flush()
            os.fsync(fh.fileno())

        # Attempt to set restrictive permissions on the temp file.
        try:
            tmp_path.chmod(0o600)
        except OSError:
            pass

        # Atomic replace
        os.replace(str(tmp_path), str(path))

        # Ensure final file permissions
        try:
            path.chmod(0o600)
        except OSError:
            pass
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
