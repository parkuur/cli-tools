"""Integration tests for the 'pin' CLI behavior."""

# pylint: disable=import-outside-toplevel,missing-function-docstring,unused-argument

import subprocess
from collections.abc import Callable

import pytest

Runner = Callable[..., subprocess.CompletedProcess[str]]


@pytest.mark.integration
def test_pin_current_dir(run_tp: Runner) -> None:
    res = run_tp("-p", "work")
    assert res.returncode == 0
    assert res.stdout == ""
    res2 = run_tp("-s", "work")
    assert res2.returncode == 0
    assert res2.stdout == ""


@pytest.mark.integration
def test_pin_explicit_path(run_tp: Runner) -> None:
    res = run_tp("-p", "work", "/tmp")
    assert res.returncode == 0
    shown = run_tp("-s", "work")
    assert shown.returncode == 0
    assert "/tmp" in shown.stderr.replace("\\", "/")


@pytest.mark.integration
def test_pin_conflict(run_tp: Runner) -> None:
    run_tp("-p", "work")
    r = run_tp("-p", "work")
    assert r.returncode == 3


@pytest.mark.integration
def test_pin_overwrite(run_tp: Runner) -> None:
    run_tp("-p", "work", "/a")
    r = run_tp("-p", "--force", "work", "/b")
    assert r.returncode == 0
    shown = run_tp("-s", "work")
    assert "/b" in shown.stderr.replace("\\", "/")


@pytest.mark.integration
def test_pin_invalid_alias_slash(run_tp: Runner) -> None:
    r = run_tp("-p", "bad/alias")
    assert r.returncode == 5


@pytest.mark.integration
def test_pin_stdout_is_empty(run_tp: Runner) -> None:
    r = run_tp("-p", "work")
    assert r.stdout == ""
