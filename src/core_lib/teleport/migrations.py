"""Database migrations for the teleport tool."""

import sqlite3

from core_lib.common.db import Migration


def _v001_forward(conn: sqlite3.Connection) -> None:
    sql = """
    CREATE TABLE IF NOT EXISTS tp_aliases (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        alias       TEXT    NOT NULL UNIQUE COLLATE NOCASE,
        path        TEXT    NOT NULL,
        created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
        updated_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
        visit_count INTEGER NOT NULL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS tp_history (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        alias_id    INTEGER REFERENCES tp_aliases(id) ON DELETE SET NULL,
        path        TEXT    NOT NULL,
        action      TEXT    NOT NULL,
        occurred_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
    );

    CREATE INDEX IF NOT EXISTS idx_tp_alias_path ON tp_aliases(path);
    """
    conn.executescript(sql)


MIGRATIONS: list[Migration] = [
    Migration(version=1, name="v001_initial", forward=_v001_forward),
]
