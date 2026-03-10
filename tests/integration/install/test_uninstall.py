import os
import subprocess
import sys
from pathlib import Path

import pytest


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


def test_uninstall_removes_marker_and_restores_backup(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    bashrc = home / ".bashrc"
    original = "# original content\necho original\n"
    bashrc.write_text(original, encoding="utf-8")

    # install
    cp = _run_installer(script, ["bash"], home, data)
    assert cp.returncode == 0
    assert "teleport snippet" in bashrc.read_text(encoding="utf-8")

    # uninstall
    cp2 = _run_installer(script, ["bash", "--uninstall"], home, data)
    assert cp2.returncode == 0

    # manifest should no longer have the marker
    manifest = data / "install_manifest.json"
    assert manifest.exists()
    content = manifest.read_text(encoding="utf-8")
    assert "teleport#tp.bash" not in content

    # backup should have been restored
    final = bashrc.read_text(encoding="utf-8")
    assert final.startswith("# original content")


def test_uninstall_no_backup_graceful(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    bashrc = home / ".bashrc"
    original = "# original content\necho original\n"
    bashrc.write_text(original, encoding="utf-8")

    # install then delete backup manually
    cp = _run_installer(script, ["bash"], home, data)
    assert cp.returncode == 0

    # delete all backups
    backups_dir = data / "backups" / "teleport"
    if backups_dir.exists():
        for f in backups_dir.iterdir():
            f.unlink()

    # uninstall should still succeed and remove marker
    cp2 = _run_installer(script, ["bash", "--uninstall"], home, data)
    assert cp2.returncode == 0
    assert "teleport snippet" not in bashrc.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("shell", "profile_rel", "marker"),
    [
        ("fish", ".config/fish/config.fish", "teleport#tp.fish"),
        ("powershell", "Documents/PowerShell/Microsoft.PowerShell_profile.ps1", "teleport#tp.ps1"),
        ("cmd", "init.bat", "teleport#tp.bat"),
    ],
)
def test_uninstall_uses_shell_specific_marker(
    tmp_path: Path,
    shell: str,
    profile_rel: str,
    marker: str,
) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    cp = _run_installer(script, [shell], home, data)
    assert cp.returncode == 0

    profile = home / profile_rel
    assert profile.exists()
    assert "teleport snippet" in profile.read_text(encoding="utf-8")

    cp2 = _run_installer(script, [shell, "--uninstall"], home, data)
    assert cp2.returncode == 0
    assert "teleport snippet" not in profile.read_text(encoding="utf-8")

    manifest_path = data / "install_manifest.json"
    content = manifest_path.read_text(encoding="utf-8")
    assert marker not in content


def test_uninstall_missing_profile_is_noop(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    cp = _run_installer(script, ["bash", "--uninstall"], home, data)
    assert cp.returncode == 0


def test_uninstall_removes_manifest_entry(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    assert _run_installer(script, ["bash"], home, data).returncode == 0
    cp = _run_installer(script, ["bash", "--uninstall"], home, data)
    assert cp.returncode == 0
    content = (data / "install_manifest.json").read_text(encoding="utf-8")
    assert "teleport#tp.bash" not in content


def test_uninstall_exit_0_on_success(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    assert _run_installer(script, ["bash"], home, data).returncode == 0
    cp = _run_installer(script, ["bash", "--uninstall"], home, data)
    assert cp.returncode == 0
