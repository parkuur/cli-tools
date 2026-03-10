"""Integration tests for the 'unpin' CLI behavior."""

# pylint: disable=import-outside-toplevel,missing-function-docstring

import subprocess
from collections.abc import Callable

import pytest

Runner = Callable[..., subprocess.CompletedProcess[str]]


@pytest.mark.integration
def test_unpin_existing(run_tp: Runner) -> None:
    run_tp("-p", "x")
    r = run_tp("-u", "x")
    assert r.returncode == 0
    assert r.stdout == ""


@pytest.mark.integration
def test_unpin_missing(run_tp: Runner) -> None:
    r = run_tp("-u", "nope")
    assert r.returncode == 2


@pytest.mark.integration
def test_unpin_stdout_is_empty(run_tp: Runner) -> None:
    run_tp("-p", "x")
    r = run_tp("-u", "x")
    assert r.stdout == ""
