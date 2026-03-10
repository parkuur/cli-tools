"""Integration tests verifying CLI exit code mapping."""

import os
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

Runner = Callable[..., subprocess.CompletedProcess[str]]


@pytest.mark.integration
def test_exit_0_on_success(run_tp: Runner) -> None:
    r = run_tp("-p", "work", "/tmp")
    assert r.returncode == 0


@pytest.mark.integration
def test_exit_2_alias_not_found(run_tp: Runner) -> None:
    r = run_tp("missing")
    assert r.returncode == 2


@pytest.mark.integration
def test_exit_3_alias_conflict(run_tp: Runner) -> None:
    run_tp("-p", "work", "/tmp")
    r = run_tp("-p", "work", "/tmp")
    assert r.returncode == 3


@pytest.mark.integration
def test_exit_4_storage_error(
    run_tp: Runner,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = run_tp
    bad_base_file = tmp_path / "blocked"
    bad_base_file.write_text("x", encoding="utf-8")
    monkeypatch.setenv("CLI_TOOLS_DATA_DIR", str(bad_base_file))
    env = {**os.environ, "CLI_TOOLS_DATA_DIR": str(bad_base_file)}
    r = subprocess.run(
        ["uv", "run", "tp-cli", "-p", "work", "/tmp"],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert r.returncode == 4


@pytest.mark.integration
def test_exit_5_invalid_path(run_tp: Runner) -> None:
    bad_path = f"{Path('/tmp')}\ninvalid"
    r = run_tp("-p", "work", bad_path)
    assert r.returncode == 5
