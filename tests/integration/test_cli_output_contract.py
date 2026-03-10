"""Integration tests verifying stdout/stderr output contract for tp-cli."""

import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

Runner = Callable[..., subprocess.CompletedProcess[str]]


@pytest.mark.integration
def test_jump_writes_path_to_stdout_only(run_tp: Runner) -> None:
    run_tp("-p", "work", "/tmp")
    r = run_tp("work")
    assert r.returncode == 0
    assert r.stdout.strip() == str(Path("/tmp").resolve())
    assert r.stderr == ""


@pytest.mark.integration
def test_human_output_goes_to_stderr(run_tp: Runner) -> None:
    r = run_tp("-p", "work", "/tmp")
    assert r.returncode == 0
    assert r.stdout == ""
    assert r.stderr.strip() != ""


@pytest.mark.integration
def test_stdout_is_machine_parseable(run_tp: Runner) -> None:
    run_tp("-p", "work", "/tmp")
    r = run_tp("work")
    out = r.stdout.strip()
    assert r.returncode == 0
    assert out == str(Path(out))


@pytest.mark.integration
def test_stdout_empty_on_non_jump_commands(run_tp: Runner) -> None:
    run_tp("-p", "work", "/tmp")
    assert run_tp("-p", "x", "/tmp").stdout == ""
    assert run_tp("-u", "x").stdout == ""
    assert run_tp("-s").stdout == ""
