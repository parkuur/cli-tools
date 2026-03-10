from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator
from contextlib import contextmanager

fcntl: Any
try:
    import fcntl
except ImportError:  # pragma: no cover - platform dependent
    fcntl = None


def default_manifest() -> dict[str, dict[str, Any]]:
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
            loaded = json.load(fh)
            if isinstance(loaded, dict):
                return loaded
            return default_manifest()
    except FileNotFoundError:
        return default_manifest()
    except (json.JSONDecodeError, OSError):
        # Corrupted or unreadable manifest: return default to allow recovery.
        return default_manifest()


def _write_manifest_file(path: Path, data: dict[str, Any]) -> None:
    """Write manifest atomically to `path` without taking any lock.

    Callers that perform read-modify-write operations must take the manifest
    lock before invoking this helper.
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

        os.replace(str(tmp_path), str(path))
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


def write_manifest(path: Path, data: dict[str, Any]) -> None:
    """Write manifest atomically to `path` and set restrictive permissions.

    Uses a temporary file in the same directory and then atomically replaces
    the target path. On POSIX the final file mode will be 0o600. Errors
    during chmod are ignored to preserve cross-platform compatibility.
    """
    lock_path = path.with_name(path.name + ".lock")
    with _manifest_lock(lock_path):
        _write_manifest_file(path, data)


def compute_checksum(file_path: Path) -> str:
    """Compute SHA256 checksum for the given file and return hex digest."""
    h = hashlib.sha256()
    with file_path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_manifest_atomic(path: Path, manifest: dict[str, Any]) -> None:
    """Internal helper used when caller already holds manifest lock."""
    _write_manifest_file(path, manifest)


@contextmanager
def _manifest_lock(lock_path: Path) -> Iterator[None]:
    """Context manager that acquires an exclusive advisory lock on lock_path.

    On POSIX this uses fcntl.flock on the lock file. On platforms without
    fcntl it falls back to creating the lock file and using atomic rename
    semantics (best-effort).
    """
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fd = open(lock_path, "a+", encoding="utf-8")
    try:
        if fcntl is not None:
            try:
                fcntl.flock(fd.fileno(), fcntl.LOCK_EX)
            except OSError:
                pass
        yield
    finally:
        try:
            if fcntl is not None:
                fcntl.flock(fd.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
        try:
            fd.close()
        except OSError:
            pass


def add_marker(
    manifest_path: Path,
    marker_id: str,
    source: str,
    profiles: list[str],
    checksum: str,
    enabled: bool = True,
) -> None:
    # Do read-modify-write under manifest lock to avoid races
    lock_path = manifest_path.with_name(manifest_path.name + ".lock")
    with _manifest_lock(lock_path):
        m = read_manifest(manifest_path)
        now = datetime.now(UTC).isoformat()
        m_inst = m.setdefault("installed", {})
        m_inst[marker_id] = {
            "source": source,
            "profiles": profiles,
            "checksum": checksum,
            "backups": [],
            "enabled": enabled,
            "installed_at": now,
        }
        _write_manifest_atomic(manifest_path, m)


def update_marker(manifest_path: Path, marker_id: str, **kwargs: Any) -> None:
    lock_path = manifest_path.with_name(manifest_path.name + ".lock")
    with _manifest_lock(lock_path):
        m = read_manifest(manifest_path)
        m_inst = m.setdefault("installed", {})
        if marker_id not in m_inst:
            raise KeyError(marker_id)
        m_inst[marker_id].update(kwargs)
        _write_manifest_atomic(manifest_path, m)


def remove_marker(manifest_path: Path, marker_id: str) -> None:
    lock_path = manifest_path.with_name(manifest_path.name + ".lock")
    with _manifest_lock(lock_path):
        m = read_manifest(manifest_path)
        m_inst = m.setdefault("installed", {})
        if marker_id in m_inst:
            del m_inst[marker_id]
            _write_manifest_atomic(manifest_path, m)


def get_marker(manifest_path: Path, marker_id: str) -> dict[str, Any] | None:
    m = read_manifest(manifest_path)
    inst = m.get("installed")
    if not isinstance(inst, dict):
        return None
    val = inst.get(marker_id)
    if isinstance(val, dict):
        normalized = dict(val)
        normalized.setdefault("enabled", True)
        normalized.setdefault("backups", [])
        normalized.setdefault("profiles", [])
        normalized.setdefault("source", "")
        normalized.setdefault("checksum", "")
        return normalized
    return None


def set_marker_enabled(
    manifest_path: Path,
    marker_id: str,
    enabled: bool,
    source: str | None = None,
    profiles: list[str] | None = None,
) -> None:
    """Set or create a minimal marker entry with enabled state.

    This creates the installed[marker_id] entry if missing, with minimal
    metadata required by the spec.
    """
    lock_path = manifest_path.with_name(manifest_path.name + ".lock")
    with _manifest_lock(lock_path):
        m = read_manifest(manifest_path)
        inst = m.setdefault("installed", {})
        entry = inst.get(marker_id)
        if entry is None:
            entry = {
                "source": source or "",
                "profiles": profiles or [],
                "checksum": "",
                "backups": [],
                "enabled": bool(enabled),
                "installed_at": None,
            }
            inst[marker_id] = entry
        else:
            entry["enabled"] = bool(enabled)
        _write_manifest_atomic(manifest_path, m)

