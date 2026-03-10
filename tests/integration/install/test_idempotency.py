import json
import os
import subprocess
import sys
from pathlib import Path


def _run_installer(
    script: Path, args: list[str], tmp_home: Path, tmp_data: Path
) -> subprocess.CompletedProcess[str]:
    env = {**os.environ}
    env["HOME"] = str(tmp_home)
    env["CLI_TOOLS_DATA_DIR"] = str(tmp_data)
    env["PYTHONPATH"] = str(Path.cwd() / "src")
    venv_bin = str(Path(sys.executable).parent)
    env["PATH"] = venv_bin + os.pathsep + env.get("PATH", "")
    return subprocess.run(
        ["bash", str(script), *args],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def test_second_install_is_noop(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    # first install
    cp1 = _run_installer(script, ["bash"], home, data)
    assert cp1.returncode == 0
    bashrc = home / ".bashrc"
    before = bashrc.read_text(encoding="utf-8")

    # second install should be noop (no change)
    cp2 = _run_installer(script, ["bash"], home, data)
    assert cp2.returncode == 0
    after = bashrc.read_text(encoding="utf-8")
    assert before == after


def test_multiple_installs_do_not_duplicate_markers(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    for _ in range(5):
        cp = _run_installer(script, ["bash"], home, data)
        assert cp.returncode == 0

    bashrc = home / ".bashrc"
    content = bashrc.read_text(encoding="utf-8")
    # expect single marker header and footer pair
    assert content.count("teleport snippet: tp.bash") == 2


def test_install_overwrites_manually_edited_marker_block(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    # install
    cp = _run_installer(script, ["bash"], home, data)
    assert cp.returncode == 0
    bashrc = home / ".bashrc"
    text = bashrc.read_text(encoding="utf-8")
    # insert manual edit directly inside marker block
    marker_line = "# >>> teleport snippet: tp.bash (id: teleport#tp.bash)\n"
    modified = text.replace(marker_line, marker_line + "# manual edit\n")
    bashrc.write_text(modified, encoding="utf-8")

    # run installer again - should replace marker with canonical snippet (no manual edit)
    cp2 = _run_installer(script, ["bash"], home, data)
    assert cp2.returncode == 0
    final = bashrc.read_text(encoding="utf-8")
    assert "# manual edit" not in final


def test_install_after_snippet_update_replaces_block_and_creates_backup(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    snippet = Path.cwd() / "src" / "cli_layer" / "shell_snippets" / "tp.bash"
    orig = snippet.read_text(encoding="utf-8")

    try:
        # initial install
        cp1 = _run_installer(script, ["bash"], home, data)
        assert cp1.returncode == 0

        # modify snippet source
        snippet.write_text(orig + "\n# updated\n", encoding="utf-8")

        # run installer again
        cp2 = _run_installer(script, ["bash"], home, data)
        assert cp2.returncode == 0

        # manifest should have backups recorded
        manifest = data / "install_manifest.json"
        content = manifest.read_text(encoding="utf-8")
        assert "backups" in content
    finally:
        snippet.write_text(orig, encoding="utf-8")


def test_idempotent_across_shell_changes(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    cp1 = _run_installer(script, ["bash"], home, data)
    assert cp1.returncode == 0
    before = (home / ".bashrc").read_text(encoding="utf-8")

    cp2 = _run_installer(script, ["bash"], home, data)
    assert cp2.returncode == 0
    after = (home / ".bashrc").read_text(encoding="utf-8")
    assert before == after

    cp3 = _run_installer(script, ["zsh"], home, data)
    assert cp3.returncode == 0
    assert (home / ".zshrc").exists()
    assert (home / ".bashrc").read_text(encoding="utf-8") == after


def test_reinstall_after_uninstall(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    assert _run_installer(script, ["bash"], home, data).returncode == 0
    assert _run_installer(script, ["bash", "--uninstall"], home, data).returncode == 0
    cp = _run_installer(script, ["bash"], home, data)
    assert cp.returncode == 0
    assert "teleport snippet" in (home / ".bashrc").read_text(encoding="utf-8")
    assert "teleport#tp.bash" in (data / "install_manifest.json").read_text(encoding="utf-8")


def test_manifest_corruption_recovery(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    assert _run_installer(script, ["bash"], home, data).returncode == 0
    manifest_path = data / "install_manifest.json"
    manifest_path.write_text("{not valid json", encoding="utf-8")

    cp = _run_installer(script, ["bash"], home, data)
    assert cp.returncode == 0
    loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "installed" in loaded


def test_checksum_mismatch_triggers_update(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    assert _run_installer(script, ["bash"], home, data).returncode == 0
    manifest_path = data / "install_manifest.json"
    loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
    loaded["installed"]["teleport#tp.bash"]["checksum"] = "deadbeef"
    manifest_path.write_text(json.dumps(loaded), encoding="utf-8")

    cp = _run_installer(script, ["bash"], home, data)
    assert cp.returncode == 0
    assert "[update]" in cp.stderr or "[install]" in cp.stderr

    fixed = json.loads(manifest_path.read_text(encoding="utf-8"))
    checksum = fixed["installed"]["teleport#tp.bash"]["checksum"]
    assert checksum != "deadbeef"
