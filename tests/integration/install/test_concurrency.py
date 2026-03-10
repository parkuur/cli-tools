import os
import subprocess
import sys
from pathlib import Path


def _run_installer_async(
    script: Path, args: list[str], tmp_home: Path, tmp_data: Path
) -> subprocess.Popen[str]:
    env = {**os.environ}
    env["HOME"] = str(tmp_home)
    env["CLI_TOOLS_DATA_DIR"] = str(tmp_data)
    env["PYTHONPATH"] = str(Path.cwd() / "src")
    venv_bin = str(Path(sys.executable).parent)
    env["PATH"] = venv_bin + os.pathsep + env.get("PATH", "")
    return subprocess.Popen(["bash", str(script), *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)


def test_installer_locks_manifest_during_write(tmp_path: Path) -> None:
    script = Path.cwd() / "scripts" / "install-shell-snippet.sh"
    home = tmp_path / "home"
    data = tmp_path / "data"
    home.mkdir()
    data.mkdir()

    # spawn two installers concurrently
    p1 = _run_installer_async(script, ["bash"], home, data)
    p2 = _run_installer_async(script, ["bash"], home, data)

    p1.communicate()
    p2.communicate()
    # both should exit successfully
    assert p1.returncode == 0
    assert p2.returncode == 0

    # manifest must exist and be valid JSON
    manifest = data / "install_manifest.json"
    assert manifest.exists()
    # quick parse check
    import json

    with manifest.open("r", encoding="utf-8") as fh:
        parsed = json.load(fh)
    assert isinstance(parsed, dict)
    assert "installed" in parsed
