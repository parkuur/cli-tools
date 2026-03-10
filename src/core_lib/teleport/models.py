"""Pydantic models for teleport aliases and history entries.

Defines `Alias` and `HistoryEntry` used throughout the teleport service and
database layers.
"""

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, field_validator


class Alias(BaseModel):
    """Represents a pinned alias pointing to a filesystem path."""

    id: int | None = None
    alias: str
    path: str
    created_at: datetime
    updated_at: datetime
    visit_count: int = 0

    @field_validator("path")
    @classmethod
    def path_no_newlines(cls, v: str) -> str:
        """Ensure the stored path does not contain newline characters."""
        if "\n" in v or "\r" in v:
            raise ValueError("Path must not contain newline characters")
        return v

    def as_path(self) -> Path:
        """Return the alias path as a :class:`pathlib.Path` instance."""
        return Path(self.path)


class HistoryEntry(BaseModel):
    """A recorded history entry for alias usage."""

    id: int | None = None
    alias_id: int | None = None
    path: str
    action: str
    occurred_at: datetime
