"""Integration tests for the 'show' CLI behavior."""

# pylint: disable=import-outside-toplevel,missing-function-docstring

import subprocess
from collections.abc import Callable

import pytest

Runner = Callable[..., subprocess.CompletedProcess[str]]


@pytest.mark.integration
def test_show_all_empty(run_tp: Runner) -> None:
    r = run_tp("-s")
    assert r.returncode == 0
    assert "no aliases" in r.stderr.lower()
    assert r.stdout == ""


@pytest.mark.integration
def test_show_all_table(run_tp: Runner) -> None:
    run_tp("-p", "a", "/tmp")
    run_tp("-p", "b", "/var/tmp")
    r = run_tp("-s")
    assert r.returncode == 0
    assert "a" in r.stderr
    assert "b" in r.stderr
    assert r.stdout == ""


@pytest.mark.integration
def test_show_single(run_tp: Runner) -> None:
    run_tp("-p", "work", "/tmp")
    r = run_tp("-s", "work")
    assert r.returncode == 0
    assert "/tmp" in r.stderr
    assert r.stdout == ""


@pytest.mark.integration
def test_show_single_missing(run_tp: Runner) -> None:
    r = run_tp("-s", "missing")
    assert r.returncode == 2
    assert "not found" in r.stderr.lower()
    assert r.stdout == ""


@pytest.mark.integration
def test_show_stdout_always_empty(run_tp: Runner) -> None:
    run_tp("-p", "work", "/tmp")
    assert run_tp("-s").stdout == ""
    assert run_tp("-s", "work").stdout == ""
