"""Database helpers and migration runner utilities.

This module provides a thin wrapper around sqlite3 to open a connection and
to run a sequence of migrations for a named tool.
"""

import hashlib
import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from core_lib.common import exceptions


@dataclass(frozen=True, slots=True)
class Migration:
    """Represents a single migration with a forward step.

    The ``forward`` callable is invoked with a sqlite3 connection to apply
    schema changes for the migration.
    """
    version: int
    name: str
    forward: Callable[[sqlite3.Connection], None]


_COMMON_DDL = (
    "CREATE TABLE IF NOT EXISTS _migrations (\n"
    "    id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
    "    tool TEXT NOT NULL,\n"
    "    version INTEGER NOT NULL,\n"
    "    name TEXT NOT NULL,\n"
    "    applied_at TEXT NOT NULL DEFAULT (\n"
    "        strftime('%Y-%m-%dT%H:%M:%fZ', 'now')\n"
    "    ),\n"
    "    checksum TEXT,\n"
    "    UNIQUE(tool, version)\n"
    ");\n\n"
    "CREATE TABLE IF NOT EXISTS metadata (\n"
    "    tool TEXT NOT NULL,\n"
    "    key TEXT NOT NULL,\n"
    "    value TEXT,\n"
    "    PRIMARY KEY (tool, key)\n"
    ");\n"
)


def open_db(db_path: Path) -> sqlite3.Connection:
    """Open a sqlite3 connection and configure recommended pragmas."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    # Use default isolation_level so we can manage transactions with BEGIN/COMMIT
    conn = sqlite3.connect(str(db_path), timeout=5.0)
    # ensure WAL mode before setting row factory so PRAGMA returns scalar
    conn.execute("PRAGMA journal_mode = wal")
    conn.row_factory = sqlite3.Row
    # set foreign keys and busy timeout
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def ensure_common_schema(conn: sqlite3.Connection) -> None:
    """Create the common schema used by all tools if missing.

    This function executes the shared DDL for all tools. Any unexpected
    errors are wrapped in :class:`exceptions.StorageError`.
    """
    try:
        cur = conn.cursor()
        cur.executescript(_COMMON_DDL)
    except Exception as exc:  # pragma: no cover - defensive
        raise exceptions.StorageError(str(exc))


def _max_applied_version(conn: sqlite3.Connection, tool: str) -> int:
    """Return the maximum applied migration version for ``tool`` or 0."""
    cur = conn.execute(
        "SELECT MAX(version) FROM _migrations WHERE tool = ?",
        (tool,),
    )
    row = cur.fetchone()
    if row is None:
        return 0
    v = row[0]
    return v or 0


def run_tool_migrations(
    conn: sqlite3.Connection,
    tool: str,
    migrations: list[Migration],
) -> None:
    """Run the given migrations for ``tool`` in order.

    Migrations with a version higher than the currently-applied maximum are
    executed in sequence. Each migration is applied inside an explicit
    transaction and recorded in the ``_migrations`` table.
    """
    ensure_common_schema(conn)
    applied_max = _max_applied_version(conn, tool)
    to_apply = [m for m in migrations if m.version > applied_max]

    for m in to_apply:
        try:
            cur = conn.cursor()
            cur.execute("BEGIN")
            # call forward with the connection
            m.forward(conn)
            checksum = hashlib.sha256(repr(m).encode()).hexdigest()
            cur.execute(
                (
                    "INSERT INTO _migrations(tool, version, name, checksum) "
                    "VALUES (?, ?, ?, ?)"
                ),
                (tool, m.version, m.name, checksum),
            )
            cur.execute("COMMIT")
        except Exception as exc:
            cur.execute("ROLLBACK")
            raise exceptions.MigrationError(str(exc))
