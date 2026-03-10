"""Utility helpers used across the codebase.

The functions in this module provide small, well-tested helpers for input
validation used by the CLI and service layers.
"""

from core_lib.common.exceptions import InvalidPathError


def validate_path(path: str) -> None:
    """Validate that ``path`` does not contain control characters.

    Raises :class:`InvalidPathError` when validation fails.
    """
    if "\n" in path or "\r" in path:
        raise InvalidPathError("Path must not contain newline or carriage return")


def sanitize_alias(alias: str) -> str:
    """Return a trimmed alias string ensuring it is non-empty and safe.

    Raises ``ValueError`` when the alias is empty or contains path separators.
    """
    s = alias.strip()
    if not s:
        raise ValueError("alias must not be empty")
    if "/" in s or "\\" in s:
        raise ValueError("alias must not contain path separators")
    return s
