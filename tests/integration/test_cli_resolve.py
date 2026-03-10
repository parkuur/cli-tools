"""Integration tests for the 'resolve' CLI behavior."""

# pylint: disable=import-outside-toplevel,missing-function-docstring

import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

Runner = Callable[..., subprocess.CompletedProcess[str]]


@pytest.mark.integration
def test_resolve_known_alias(run_tp: Runner) -> None:
    run_tp("-p", "work", "/tmp")
    r = run_tp("work")
    assert r.returncode == 0
    assert r.stdout.strip() == str(Path("/tmp").resolve())
    assert r.stderr == ""


@pytest.mark.integration
def test_resolve_unknown_alias(run_tp: Runner) -> None:
    r = run_tp("missing")
    assert r.returncode == 2
    assert r.stdout == ""
    assert "not found" in r.stderr.lower()


@pytest.mark.integration
def test_resolve_no_args_prints_home(run_tp: Runner) -> None:
    r = run_tp()
    assert r.returncode == 0
    assert r.stdout == f"{Path.home()}\n"


@pytest.mark.integration
def test_resolve_increments_visit_count(run_tp: Runner) -> None:
    run_tp("-p", "work", "/tmp")
    run_tp("work")
    run_tp("work")
    shown = run_tp("-s")
    assert shown.returncode == 0
    assert "2" in shown.stderr


@pytest.mark.integration
def test_resolve_stdout_single_line(run_tp: Runner) -> None:
    run_tp("-p", "work", "/tmp")
    r = run_tp("work")
    lines = [line for line in r.stdout.splitlines() if line]
    assert r.returncode == 0
    assert len(lines) == 1
    assert lines[0] == lines[0].strip()
