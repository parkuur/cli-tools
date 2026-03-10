import json
import os
from pathlib import Path



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
