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


def test_no_tp_flag_skips_teleport_install(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    # disable tp
    cp = _run_installer(script, ["--no-tp"], home, data)
    assert cp.returncode == 0

    manifest = data / "install_manifest.json"
    assert manifest.exists()
    content = manifest.read_text(encoding="utf-8")
    assert "teleport#tp.bash" in content
    assert "\"enabled\": false" in content

    # ensure no profile changes
    bashrc = home / ".bashrc"
    assert not bashrc.exists()


def test_install_after_no_tp_flag_respects_previous_choice(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    # disable tp
    cp = _run_installer(script, ["--no-tp"], home, data)
    assert cp.returncode == 0

    # run installer without flags (should respect manifest and skip)
    cp2 = _run_installer(script, ["bash"], home, data)
    assert cp2.returncode == 0
    bashrc = home / ".bashrc"
    assert not bashrc.exists()


def test_enabled_flag_default_true_for_new_installs(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    cp = _run_installer(script, ["bash"], home, data)
    assert cp.returncode == 0
    manifest = data / "install_manifest.json"
    assert manifest.exists()
    content = manifest.read_text(encoding="utf-8")
    assert "\"enabled\": true" in content


def test_dry_run_with_no_tp_flag_is_side_effect_free(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    cp = _run_installer(script, ["--dry-run", "--no-tp"], home, data)
    assert cp.returncode == 0
    assert "[plan]" in cp.stderr
    assert not (data / "install_manifest.json").exists()


def test_explicit_enable_overrides_disabled_state(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    cp = _run_installer(script, ["--no-tp"], home, data)
    assert cp.returncode == 0

    cp2 = _run_installer(script, ["--tp"], home, data)
    assert cp2.returncode == 0

    manifest = data / "install_manifest.json"
    content = manifest.read_text(encoding="utf-8")
    assert "\"enabled\": true" in content


def test_no_tp_flag_records_disabled_state(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    cp = _run_installer(script, ["--no-tp"], home, data)
    assert cp.returncode == 0
    content = (data / "install_manifest.json").read_text(encoding="utf-8")
    assert "teleport#tp.bash" in content
    assert "\"enabled\": false" in content


def test_uninstall_with_no_tp_flag_noops_for_disabled_tool(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    assert _run_installer(script, ["--no-tp"], home, data).returncode == 0
    cp = _run_installer(script, ["bash", "--uninstall", "--no-tp"], home, data)
    assert cp.returncode == 0


def test_invalid_tool_flag_fails_with_exit_1(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    cp = _run_installer(script, ["--no-invalid-tool"], home, data)
    assert cp.returncode == 1


def test_flag_pattern_consistent_across_tools(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    cp = _run_installer(script, ["--help"], home, data)
    assert cp.returncode == 0
    assert "--no-tp" in cp.stdout
    assert "--tp" in cp.stdout
