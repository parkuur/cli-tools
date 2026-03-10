"""Helpers for storing small key/value metadata in the DB.

The metadata table is a simple key/value store used by the teleport service
to persist small pieces of state such as the previous path.
"""

import sqlite3


def get_metadata(conn: sqlite3.Connection, tool: str, key: str) -> str | None:
    """Return the metadata value for (tool, key) or ``None`` if missing.

    The DB returns a row when present, otherwise ``None``.
    """
    cur = conn.execute(
        "SELECT value FROM metadata WHERE tool = ? AND key = ?",
        (tool, key),
    )
    row = cur.fetchone()
    if row is None:
        return None
    value = row[0]
    if value is None or isinstance(value, str):
        return value
    return str(value)


def set_metadata(conn: sqlite3.Connection, tool: str, key: str, value: str) -> None:
    """Insert or update a metadata value for the given tool/key."""
    conn.execute(
        (
            "INSERT INTO metadata(tool, key, value) VALUES (?, ?, ?) "
            "ON CONFLICT(tool, key) DO UPDATE SET value = excluded.value"
        ),
        (tool, key, value),
    )
