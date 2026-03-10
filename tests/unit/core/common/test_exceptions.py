"""Unit tests for custom exception classes."""

# pylint: disable=import-outside-toplevel,missing-function-docstring
import pytest

from core_lib.common import exceptions as exc_module

pytestmark = pytest.mark.unit


def test_all_exceptions_inherit_cli_tools_error() -> None:
    assert issubclass(exc_module.AliasNotFoundError, exc_module.CliToolsError)
    assert issubclass(exc_module.AliasConflictError, exc_module.CliToolsError)
    assert issubclass(exc_module.StorageError, exc_module.CliToolsError)
    assert issubclass(exc_module.InvalidPathError, exc_module.CliToolsError)


def test_migration_error_inherits_storage_error() -> None:
    assert issubclass(exc_module.MigrationError, exc_module.StorageError)


def test_catch_base_exception() -> None:
    try:
        raise exc_module.AliasNotFoundError("x")
    except exc_module.CliToolsError:
        caught = True
    else:
        caught = False
    assert caught
