"""Exception types used by the cli-tools packages.

These lightweight exception classes make error handling in the service and
CLI layers explicit and easy to test.
"""


class CliToolsError(Exception):
    """Base exception for all cli-tools errors."""


class AliasNotFoundError(CliToolsError):
    """Raised when an alias does not exist in the database."""


class AliasConflictError(CliToolsError):
    """Raised when trying to pin an alias that already exists."""


class StorageError(CliToolsError):
    """Raised on SQLite errors, I/O errors, or migration failures."""


class MigrationError(StorageError):
    """Raised when a schema migration fails to apply."""


class InvalidPathError(CliToolsError):
    """Raised when a path fails validation (e.g. contains newlines)."""
