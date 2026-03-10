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
    # Ensure the project's src is on PYTHONPATH for module imports
    env["PYTHONPATH"] = str(Path.cwd() / "src")
    # Make sure the venv/python used by the test is on PATH so `python -m` works
    venv_bin = str(Path(sys.executable).parent)
    env["PATH"] = venv_bin + os.pathsep + env.get("PATH", "")
    return subprocess.run(
        ["bash", str(script), *args],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def test_install_creates_manifest(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    cp = _run_installer(script, ["bash"], home, data)
    assert cp.returncode == 0
    manifest = data / "install_manifest.json"
    assert manifest.exists()


def test_install_supports_zsh(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    cp = _run_installer(script, ["zsh"], home, data)
    assert cp.returncode == 0
    zshrc = home / ".zshrc"
    assert zshrc.exists()
    content = zshrc.read_text(encoding="utf-8")
    assert "teleport snippet" in content


def test_install_supports_fish(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    cp = _run_installer(script, ["fish"], home, data)
    assert cp.returncode == 0
    fishcfg = home / ".config" / "fish" / "config.fish"
    assert fishcfg.exists()
    assert "teleport snippet" in fishcfg.read_text(encoding="utf-8")


def test_install_fails_with_exit_2_for_unsupported_shell(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    cp = _run_installer(script, ["unsupported_shell"], home, data)
    assert cp.returncode == 2


def test_install_exit_0_on_success(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    cp = _run_installer(script, ["bash"], home, data)
    assert cp.returncode == 0


def test_install_outputs_summary_to_stderr(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    cp = _run_installer(script, ["bash"], home, data)
    assert cp.returncode == 0
    assert "[summary]" in cp.stderr


def test_install_records_repo_relative_source_path(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    cp = _run_installer(script, ["bash"], home, data)
    assert cp.returncode == 0
    manifest = data / "install_manifest.json"
    content = manifest.read_text(encoding="utf-8")
    assert "src/cli_layer/shell_snippets/tp.bash" in content


def test_install_inserts_marker_block(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    cp = _run_installer(script, ["bash"], home, data)
    assert cp.returncode == 0
    bashrc = home / ".bashrc"
    text = bashrc.read_text(encoding="utf-8")
    assert ">>> teleport snippet: tp.bash (id: teleport#tp.bash)" in text
    assert "<<< teleport snippet: tp.bash" in text


def test_install_creates_backup_before_edit(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    bashrc = home / ".bashrc"
    original = "# custom\n"
    bashrc.write_text(original, encoding="utf-8")

    cp = _run_installer(script, ["bash"], home, data)
    assert cp.returncode == 0
    backups = list((data / "backups" / "teleport").glob("*.bak"))
    assert backups
    assert backups[-1].read_text(encoding="utf-8") == original


def test_install_records_marker_in_manifest(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    cp = _run_installer(script, ["bash"], home, data)
    assert cp.returncode == 0
    content = (data / "install_manifest.json").read_text(encoding="utf-8")
    assert "teleport#tp.bash" in content
    assert "\"enabled\": true" in content


def test_dry_run_reports_without_modifying(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    cp = _run_installer(script, ["bash", "--dry-run"], home, data)
    assert cp.returncode == 0
    assert "[plan]" in cp.stderr
    assert not (home / ".bashrc").exists()
    assert not (data / "install_manifest.json").exists()


def test_install_handles_nonexistent_profile_safely(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    cp = _run_installer(script, ["bash"], home, data)
    assert cp.returncode == 0
    bashrc = home / ".bashrc"
    assert bashrc.exists()
    assert "teleport snippet" in bashrc.read_text(encoding="utf-8")


def test_install_preserves_existing_profile_content(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    bashrc = home / ".bashrc"
    bashrc.write_text("export FOO=bar\n", encoding="utf-8")

    cp = _run_installer(script, ["bash"], home, data)
    assert cp.returncode == 0
    text = bashrc.read_text(encoding="utf-8")
    assert "export FOO=bar" in text
    assert "teleport snippet" in text


def test_install_creates_backup_directory_structure(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    cp = _run_installer(script, ["bash"], home, data)
    assert cp.returncode == 0
    assert (data / "backups" / "teleport").exists()


def test_multiple_profiles_supported(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    p1 = home / ".bashrc"
    p2 = home / ".bash_profile"
    cp = _run_installer(script, ["bash", "--profiles", f"{p1},{p2}"], home, data)
    assert cp.returncode == 0
    assert "teleport snippet" in p1.read_text(encoding="utf-8")
    assert "teleport snippet" in p2.read_text(encoding="utf-8")


def test_installer_respects_cli_tools_data_dir_env(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    custom_data = tmp_path / "my data dir"
    home.mkdir()
    custom_data.mkdir()

    cp = _run_installer(script, ["bash"], home, custom_data)
    assert cp.returncode == 0
    assert (custom_data / "install_manifest.json").exists()


def test_marker_block_uses_correct_comment_syntax_bash(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    cp = _run_installer(script, ["bash"], home, data)
    assert cp.returncode == 0
    text = (home / ".bashrc").read_text(encoding="utf-8")
    assert text.splitlines()[0].startswith("# >>>")


def test_marker_block_uses_correct_comment_syntax_fish(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    cp = _run_installer(script, ["fish"], home, data)
    assert cp.returncode == 0
    text = (home / ".config" / "fish" / "config.fish").read_text(encoding="utf-8")
    assert text.splitlines()[0].startswith("# >>>")


def test_installer_preserves_file_encoding(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    bashrc = home / ".bashrc"
    bashrc.write_text("echo ääkkönen\n", encoding="utf-8")

    cp = _run_installer(script, ["bash"], home, data)
    assert cp.returncode == 0
    text = bashrc.read_text(encoding="utf-8")
    assert "ääkkönen" in text


def test_installer_handles_paths_with_spaces(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    spaced = home / ".my profile.sh"
    cp = _run_installer(script, ["bash", "--profiles", str(spaced)], home, data)
    assert cp.returncode == 0
    assert spaced.exists()
    assert "teleport snippet" in spaced.read_text(encoding="utf-8")


def test_install_exit_3_on_permission_failure(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    bashrc = home / ".bashrc"
    bashrc.write_text("seed\n", encoding="utf-8")
    home.chmod(0o500)
    try:
        cp = _run_installer(script, ["bash"], home, data)
        assert cp.returncode == 3
    finally:
        home.chmod(0o700)
