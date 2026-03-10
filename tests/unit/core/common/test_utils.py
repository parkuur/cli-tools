"""Unit tests for utility helpers used across the project."""

# pylint: disable=import-outside-toplevel,missing-function-docstring

import pytest

pytestmark = pytest.mark.unit


def test_validate_path_accepts_normal_path() -> None:
    from core_lib.common.utils import validate_path

    validate_path("/tmp")


def test_validate_path_rejects_newline() -> None:
    from core_lib.common.exceptions import InvalidPathError
    from core_lib.common.utils import validate_path

    with pytest.raises(InvalidPathError):
        validate_path("/tmp\nbad")


def test_validate_path_rejects_carriage_return() -> None:
    from core_lib.common.exceptions import InvalidPathError
    from core_lib.common.utils import validate_path

    with pytest.raises(InvalidPathError):
        validate_path("/tmp\rbad")


def test_sanitize_alias_strips_whitespace() -> None:
    from core_lib.common.utils import sanitize_alias

    assert sanitize_alias("  x  ") == "x"


def test_sanitize_alias_rejects_empty() -> None:
    from core_lib.common.utils import sanitize_alias

    with pytest.raises(ValueError):
        sanitize_alias("   ")


def test_sanitize_alias_rejects_slash() -> None:
    from core_lib.common.utils import sanitize_alias

    with pytest.raises(ValueError):
        sanitize_alias("bad/alias")
