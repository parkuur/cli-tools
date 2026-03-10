"""Test fixtures used across unit and integration tests."""

# Tests intentionally use local imports in fixtures and short test functions.
# Disable the following pylint checks here only for tests:
# - import-outside-toplevel: pytest fixtures sometimes import locally
# - missing-function-docstring: tests use self-describing names
# Module docstring above satisfies missing-module-docstring.
# pylint: disable=import-outside-toplevel,missing-function-docstring,redefined-outer-name,redefined-builtin

import os
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from core_lib.teleport.service import TeleportService


@pytest.fixture()
def tmp_db_path(tmp_path: Path) -> Path:
    """Return path to a fresh, schema-initialised cli-tools.db in a temp dir."""
    from core_lib.common.db import ensure_common_schema, open_db

    db = tmp_path / "cli-tools.db"
    conn = open_db(db)
    ensure_common_schema(conn)
    conn.close()
    return db


@pytest.fixture()
def tmp_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Set CLI_TOOLS_DATA_DIR to a temp dir and return it."""
    monkeypatch.setenv("CLI_TOOLS_DATA_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture()
def teleport_service(tmp_db_path: Path) -> "TeleportService":
    """Return a TeleportService backed by a fresh temp DB."""
    from core_lib.teleport.service import TeleportService

    # Service constructor is expected to run migrations
    return TeleportService(tmp_db_path)


@pytest.fixture()
def run_tp(tmp_data_dir: Path) -> Callable[..., subprocess.CompletedProcess[str]]:
    """Return a callable that runs tp-cli with the temp data dir and returns
    a CompletedProcess with decoded stdout/stderr."""

    def _run(*args: str, input: str | None = None) -> subprocess.CompletedProcess[str]:
        env = {**os.environ, "CLI_TOOLS_DATA_DIR": str(tmp_data_dir)}
        return subprocess.run(
            ["uv", "run", "tp-cli", *args],
            capture_output=True,
            text=True,
            env=env,
            input=input,
            check=False,
        )

    return _run
