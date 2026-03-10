"""Unit tests for platform helper utilities."""

# pylint: disable=import-outside-toplevel,missing-function-docstring,unused-argument

import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def test_get_data_dir_env_override(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CLI_TOOLS_DATA_DIR", str(tmp_path))
    from core_lib.common.platform import get_data_dir

    assert get_data_dir() == tmp_path


def test_get_data_dir_macos_default(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("CLI_TOOLS_DATA_DIR", raising=False)
    monkeypatch.setattr(sys, "platform", "darwin")
    from core_lib.common.platform import get_data_dir

    expected = Path.home() / "Library" / "Application Support" / "cli-tools"
    assert get_data_dir() == expected


def test_get_data_dir_linux_xdg(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    monkeypatch.setattr(sys, "platform", "linux")
    from core_lib.common.platform import get_data_dir

    assert get_data_dir() == tmp_path / "cli-tools"


def test_get_data_dir_linux_fallback(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    monkeypatch.setattr(sys, "platform", "linux")
    from core_lib.common.platform import get_data_dir

    expected = Path.home() / ".local" / "share" / "cli-tools"
    assert get_data_dir() == expected


def test_get_data_dir_windows_localappdata(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
    from core_lib.common.platform import get_data_dir

    assert "AppData" in str(get_data_dir())


def test_get_db_path_appends_filename(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CLI_TOOLS_DATA_DIR", str(tmp_path))
    from core_lib.common.platform import get_db_path

    assert get_db_path() == tmp_path / "cli-tools.db"


def test_get_data_dir_creates_directory(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    d = tmp_path / "cli-tools"
    monkeypatch.setenv("CLI_TOOLS_DATA_DIR", str(d))
    from core_lib.common.platform import get_data_dir

    got = get_data_dir()
    assert got.exists()


def test_get_data_dir_posix_permissions(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CLI_TOOLS_DATA_DIR", str(tmp_path / "cli-tools"))
    from core_lib.common.platform import get_data_dir

    d = get_data_dir()
    mode = d.stat().st_mode
    assert (mode & 0o700) == 0o700
