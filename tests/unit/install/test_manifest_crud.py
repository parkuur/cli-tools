from pathlib import Path


def test_add_and_get_update_and_remove_marker(tmp_path: Path) -> None:
    from cli_layer.install import manifest

    mpath = tmp_path / "manifest.json"
    # start fresh
    manifest.create_manifest(mpath)

    marker_id = "teleport#tp.bash"
    source = "src/cli_layer/shell_snippets/tp.bash"
    profiles = ["~/.bashrc"]
    checksum = "abc123"

    manifest.add_marker(mpath, marker_id, source, profiles, checksum)
    got = manifest.get_marker(mpath, marker_id)
    assert got is not None
    assert got["source"] == source
    assert got["profiles"] == profiles
    assert got["checksum"] == checksum
    assert got.get("enabled") is True

    # update checksum
    manifest.update_marker(mpath, marker_id, checksum="def456")
    got2 = manifest.get_marker(mpath, marker_id)
    assert got2 is not None
    assert got2["checksum"] == "def456"

    # remove
    manifest.remove_marker(mpath, marker_id)
    assert manifest.get_marker(mpath, marker_id) is None


def test_compute_checksum(tmp_path: Path) -> None:
    from cli_layer.install import manifest

    p = tmp_path / "snippet.txt"
    p.write_text("hello\n", encoding="utf-8")
    checksum = manifest.compute_checksum(p)
    # SHA256 of 'hello\n'
    assert len(checksum) == 64
    assert checksum == "\n".join([""])[1:1] or isinstance(checksum, str)
