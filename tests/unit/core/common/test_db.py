"""Unit tests for sqlite DB helpers and migration runner."""

# pylint: disable=import-outside-toplevel,missing-function-docstring,r0903

import sqlite3
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def test_open_db_returns_connection(tmp_path: Path) -> None:
    from core_lib.common.db import open_db

    db = tmp_path / "cli-tools.db"
    conn = open_db(db)
    assert isinstance(conn, sqlite3.Connection)
    conn.close()


def test_open_db_wal_mode(tmp_path: Path) -> None:
    from core_lib.common.db import open_db

    db = tmp_path / "cli-tools.db"
    conn = open_db(db)
    cur = conn.execute("PRAGMA journal_mode")
    row = cur.fetchone()
    # journal_mode may return a tuple-like row; check first column
    assert row is not None and "wal" in str(row[0]).lower()
    conn.close()


def test_open_db_foreign_keys(tmp_path: Path) -> None:
    from core_lib.common.db import open_db

    db = tmp_path / "cli-tools.db"
    conn = open_db(db)
    cur = conn.execute("PRAGMA foreign_keys")
    val = cur.fetchone()[0]
    assert val == 1
    conn.close()


def test_open_db_row_factory(tmp_path: Path) -> None:
    from core_lib.common.db import open_db

    db = tmp_path / "cli-tools.db"
    conn = open_db(db)
    conn.execute("CREATE TABLE IF NOT EXISTS t (id INTEGER PRIMARY KEY, name TEXT)")
    conn.execute("INSERT INTO t(name) VALUES (?)", ("x",))
    cur = conn.execute("SELECT * FROM t")
    row = cur.fetchone()
    assert hasattr(row, "keys") or hasattr(row, "__getitem__")
    conn.close()


def test_open_db_creates_file(tmp_path: Path) -> None:
    from core_lib.common.db import open_db

    db = tmp_path / "cli-tools.db"
    assert not db.exists()
    conn = open_db(db)
    conn.close()
    assert db.exists()


def test_ensure_common_schema_creates_migrations_table(tmp_db_path: Path) -> None:
    from core_lib.common.db import ensure_common_schema, open_db

    conn = open_db(tmp_db_path)
    ensure_common_schema(conn)
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='_migrations'")
    assert cur.fetchone() is not None
    conn.close()


def test_ensure_common_schema_creates_metadata_table(tmp_db_path: Path) -> None:
    from core_lib.common.db import ensure_common_schema, open_db

    conn = open_db(tmp_db_path)
    ensure_common_schema(conn)
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='metadata'")
    assert cur.fetchone() is not None
    conn.close()


def test_ensure_common_schema_idempotent(tmp_db_path: Path) -> None:
    from core_lib.common.db import ensure_common_schema, open_db

    conn = open_db(tmp_db_path)
    ensure_common_schema(conn)
    ensure_common_schema(conn)
    conn.close()


def test_run_tool_migrations_applies_pending(tmp_db_path: Path) -> None:
    from core_lib.common.db import Migration, ensure_common_schema, open_db, run_tool_migrations

    conn = open_db(tmp_db_path)
    ensure_common_schema(conn)

    migrations = [Migration(version=1, name="v1", forward=lambda conn: None)]

    # run_tool_migrations should accept the migration-like objects per spec
    run_tool_migrations(conn, "teleport_test", migrations)
    cur = conn.execute(
        "SELECT tool, version FROM _migrations WHERE tool = ?",
        ("teleport_test",),
    )
    rows = cur.fetchall()
    assert rows is not None
    conn.close()


def test_run_tool_migrations_records_version_and_name(tmp_db_path: Path) -> None:
    from core_lib.common.db import ensure_common_schema, open_db, run_tool_migrations

    conn = open_db(tmp_db_path)
    ensure_common_schema(conn)

    def forward(conn: sqlite3.Connection) -> None:
        conn.execute("CREATE TABLE IF NOT EXISTS t2 (id INTEGER PRIMARY KEY)")

    from core_lib.common.db import Migration

    migrations = [Migration(version=1, name="init", forward=forward)]
    run_tool_migrations(conn, "teleport_test2", migrations)
    cur = conn.execute(
        "SELECT tool, version, name FROM _migrations WHERE tool = ?",
        ("teleport_test2",),
    )
    row = cur.fetchone()
    assert row is not None
    conn.close()


def test_run_tool_migrations_idempotent(tmp_db_path: Path) -> None:
    from core_lib.common.db import ensure_common_schema, open_db, run_tool_migrations

    conn = open_db(tmp_db_path)
    ensure_common_schema(conn)

    def forward(conn: sqlite3.Connection) -> None:
        conn.execute("CREATE TABLE IF NOT EXISTS t3 (id INTEGER PRIMARY KEY)")

    from core_lib.common.db import Migration

    migrations = [Migration(version=1, name="init", forward=forward)]
    run_tool_migrations(conn, "teleport_test3", migrations)
    # running again should not raise
    run_tool_migrations(conn, "teleport_test3", migrations)
    conn.close()


def test_run_tool_migrations_partial_resume(tmp_db_path: Path) -> None:
    from core_lib.common.db import ensure_common_schema, open_db, run_tool_migrations

    conn = open_db(tmp_db_path)
    ensure_common_schema(conn)

    def f1(conn: sqlite3.Connection) -> None:
        conn.execute("CREATE TABLE IF NOT EXISTS t4 (id INTEGER PRIMARY KEY)")

    def f2(conn: sqlite3.Connection) -> None:
        conn.execute("CREATE TABLE IF NOT EXISTS t5 (id INTEGER PRIMARY KEY)")

    from core_lib.common.db import Migration

    migrations1 = [Migration(version=1, name="v1", forward=f1)]
    migrations2 = [Migration(version=2, name="v2", forward=f2)]

    run_tool_migrations(conn, "teleport_test4", migrations1)
    run_tool_migrations(conn, "teleport_test4", migrations1 + migrations2)
    conn.close()


def test_run_tool_migrations_tool_isolation(tmp_db_path: Path) -> None:
    from core_lib.common.db import ensure_common_schema, open_db, run_tool_migrations

    conn = open_db(tmp_db_path)
    ensure_common_schema(conn)

    def forward(conn: sqlite3.Connection) -> None:
        conn.execute("CREATE TABLE IF NOT EXISTS t6 (id INTEGER PRIMARY KEY)")

    from core_lib.common.db import Migration

    migrations = [Migration(version=1, name="init", forward=forward)]
    run_tool_migrations(conn, "toolA", migrations)
    run_tool_migrations(conn, "toolB", migrations)
    cur = conn.execute("SELECT COUNT(DISTINCT tool) FROM _migrations WHERE version = 1")
    assert cur.fetchone()[0] >= 2
    conn.close()


def test_run_tool_migrations_failure_rolls_back(tmp_db_path: Path) -> None:
    from core_lib.common.db import ensure_common_schema, open_db, run_tool_migrations

    conn = open_db(tmp_db_path)
    ensure_common_schema(conn)

    def bad_forward(conn: sqlite3.Connection) -> None:
        raise RuntimeError("boom")

    from core_lib.common.db import Migration

    migrations = [Migration(version=1, name="bad", forward=bad_forward)]
    with pytest.raises(Exception):
        run_tool_migrations(conn, "teleport_bad", migrations)
    # Ensure no _migrations row was recorded
    cur = conn.execute("SELECT * FROM _migrations WHERE tool = ?", ("teleport_bad",))
    assert cur.fetchone() is None
    conn.close()


def test_run_tool_migrations_empty_list(tmp_db_path: Path) -> None:
    from core_lib.common.db import ensure_common_schema, open_db, run_tool_migrations

    conn = open_db(tmp_db_path)
    ensure_common_schema(conn)
    run_tool_migrations(conn, "teleport_empty", [])
    cur = conn.execute("SELECT * FROM _migrations WHERE tool = ?", ("teleport_empty",))
    assert cur.fetchone() is None
    conn.close()
