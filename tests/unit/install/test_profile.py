# pyright: reportMissingTypeStubs=false

from pathlib import Path


def test_detect_and_build_marker_block() -> None:
    from cli_layer.install import profile

    marker_id = "teleport#tp.bash"
    filename = "tp.bash"
    snippet = "echo hello"
    block = profile.build_marker_block(marker_id, filename, snippet, comment="#")
    assert "teleport snippet: tp.bash" in block
    assert "echo hello" in block

    text = "some line\n" + block + "\nend\n"
    rng = profile.detect_marker(text, marker_id, comment="#")
    assert rng is not None


def test_insert_marker_creates_backup_and_inserts(tmp_path: Path) -> None:
    from cli_layer.install import profile

    prof = tmp_path / ".bashrc"
    prof.write_text("# existing\necho pre\n", encoding="utf-8")

    marker_id = "teleport#tp.bash"
    filename = "tp.bash"
    snippet = "echo hello"

    backup = profile.insert_marker_into_profile(
        prof, marker_id, filename, snippet, shell="bash", tool_name="teleport"
    )
    assert backup.exists()
    content = prof.read_text(encoding="utf-8")
    assert "teleport snippet: tp.bash" in content


def test_remove_marker_from_profile(tmp_path: Path) -> None:
    from cli_layer.install import profile

    marker_id = "teleport#tp.bash"
    filename = "tp.bash"
    snippet = "echo hello"
    prof = tmp_path / ".bashrc"
    prof.write_text(profile.build_marker_block(marker_id, filename, snippet), encoding="utf-8")
    removed = profile.remove_marker_from_profile(prof, marker_id, shell="bash")
    assert removed
    assert "teleport snippet" not in prof.read_text(encoding="utf-8")


def test_remove_marker_missing_profile_returns_false(tmp_path: Path) -> None:
    from cli_layer.install import profile

    prof = tmp_path / ".missingrc"
    removed = profile.remove_marker_from_profile(prof, "teleport#tp.bash", shell="bash")
    assert removed is False
