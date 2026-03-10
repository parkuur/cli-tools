"""Integration tests for the 'previous' CLI behavior."""

# pylint: disable=import-outside-toplevel,missing-function-docstring

import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

Runner = Callable[..., subprocess.CompletedProcess[str]]


@pytest.mark.integration
def test_previous_no_history(run_tp: Runner) -> None:
    r = run_tp("-")
    assert r.returncode == 2
    assert "no previous path" in r.stderr.lower()


@pytest.mark.integration
def test_previous_after_jump(run_tp: Runner) -> None:
    run_tp("-p", "work", "/tmp")
    run_tp("work")
    r = run_tp("-")
    assert r.returncode == 0
    assert r.stdout == f"{Path.cwd()}\n"


@pytest.mark.integration
def test_previous_stdout_single_line(run_tp: Runner) -> None:
    run_tp("-p", "work", "/tmp")
    run_tp("work")
    r = run_tp("-")
    lines = [line for line in r.stdout.splitlines() if line]
    assert r.returncode == 0
    assert len(lines) == 1
