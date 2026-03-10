"""Database action helpers for teleport aliases and history.

This module contains small CRUD-style helpers used by the TeleportService
to interact with the sqlite database.
"""

import sqlite3
from datetime import UTC, datetime

from core_lib.teleport.models import Alias


def _now_iso_z() -> str:
    """Return current UTC timestamp in ISO format with trailing Z."""
    # use timezone-aware UTC and render with a trailing Z
    return datetime.now(UTC).isoformat(sep="T", timespec="microseconds").replace(
        "+00:00", "Z"
    )


def _parse_ts(s: str | None) -> datetime:
    """Parse an ISO-like timestamp produced by the DB back into datetime.

    Accepts Optional[str] because DB fields may be NULL; a missing value
    raises ValueError to signal an unexpected null timestamp.
    """
    if s is None:
        raise ValueError("timestamp is None")
    if s.endswith("Z"):
        s = s[:-1]
    return datetime.fromisoformat(s)


def _row_to_alias(row: sqlite3.Row) -> Alias:
    """Convert a sqlite3.Row into an `Alias` model instance."""
    return Alias(
        id=row["id"],
        alias=row["alias"],
        path=row["path"],
        created_at=_parse_ts(row["created_at"]),
        updated_at=_parse_ts(row["updated_at"]),
        visit_count=int(row["visit_count"]),
    )


def get_alias(conn: sqlite3.Connection, alias: str) -> Alias | None:
    """Return the Alias with the given name or ``None`` if missing.

    Comparison is case-insensitive using the database collation.
    """
    cur = conn.execute(
        "SELECT * FROM tp_aliases WHERE alias = ? COLLATE NOCASE",
        (alias,),
    )
    row = cur.fetchone()
    if row is None:
        return None
    return _row_to_alias(row)


def insert_alias(conn: sqlite3.Connection, alias: str, path: str) -> Alias:
    """Insert a new alias record and return the created Alias model.

    The record's `created_at` and `updated_at` timestamps are set to
    the current UTC time produced by :func:`_now_iso_z`.
    """
    now = _now_iso_z()
    cur = conn.execute(
        "INSERT INTO tp_aliases(alias, path, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (alias, path, now, now),
    )
    conn.commit()
    rowid = cur.lastrowid
    row = conn.execute("SELECT * FROM tp_aliases WHERE id = ?", (rowid,)).fetchone()
    return _row_to_alias(row)


def update_alias(conn: sqlite3.Connection, alias: str, path: str) -> Alias:
    """Update the path for the given alias and return the updated Alias."""
    now = _now_iso_z()
    conn.execute(
        "UPDATE tp_aliases SET path = ?, updated_at = ? WHERE alias = ? COLLATE NOCASE",
        (path, now, alias),
    )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM tp_aliases WHERE alias = ? COLLATE NOCASE",
        (alias,),
    ).fetchone()
    return _row_to_alias(row)


def delete_alias(conn: sqlite3.Connection, alias: str) -> None:
    """Delete the alias with the provided name (case-insensitive)."""
    conn.execute(
        "DELETE FROM tp_aliases WHERE alias = ? COLLATE NOCASE",
        (alias,),
    )
    conn.commit()


def list_aliases(conn: sqlite3.Connection) -> list[Alias]:
    """Return all aliases ordered by name (case-insensitive)."""
    cur = conn.execute(
        "SELECT * FROM tp_aliases ORDER BY alias COLLATE NOCASE",
    )
    return [_row_to_alias(r) for r in cur.fetchall()]


def increment_visit_count(conn: sqlite3.Connection, alias_id: int) -> None:
    """Increment the visit count for the alias with the given id."""
    conn.execute(
        "UPDATE tp_aliases SET visit_count = visit_count + 1 WHERE id = ?",
        (alias_id,),
    )
    conn.commit()


def insert_history(conn: sqlite3.Connection, alias_id: int | None, path: str, action: str) -> None:
    """Append a history row recording ``action`` for the given path/alias."""
    conn.execute(
        "INSERT INTO tp_history(alias_id, path, action) VALUES (?, ?, ?)",
        (alias_id, path, action),
    )
    conn.commit()


def prune_history(conn: sqlite3.Connection, limit: int = 1000) -> None:
    """Prune history to retain only the most recent ``limit`` entries."""
    conn.execute(
        (
            "DELETE FROM tp_history WHERE id NOT IN ("
            "SELECT id FROM tp_history ORDER BY id DESC LIMIT ?)"
        ),
        (limit,),
    )
    conn.commit()
