"""Unit tests for teleport DB migrations."""

# pylint: disable=import-outside-toplevel,missing-function-docstring

from pathlib import Path

import pytest

from core_lib.common.db import ensure_common_schema, open_db, run_tool_migrations
from core_lib.teleport import migrations as mig_mod

pytestmark = pytest.mark.unit


def test_migrations_list_not_empty() -> None:
    assert hasattr(mig_mod, "MIGRATIONS")
    assert isinstance(mig_mod.MIGRATIONS, list)
    assert len(mig_mod.MIGRATIONS) >= 1


def test_migrations_versions_sequential() -> None:
    versions = [m.version for m in mig_mod.MIGRATIONS]
    assert versions == list(range(1, len(versions) + 1))


def test_v001_creates_tp_aliases(tmp_path: Path) -> None:
    db = tmp_path / "cli-tools.db"
    conn = open_db(db)
    ensure_common_schema(conn)
    # apply only v001
    run_tool_migrations(conn, "teleport_test", [mig_mod.MIGRATIONS[0]])
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='tp_aliases'"
    )
    assert cur.fetchone() is not None
    conn.close()


def test_v001_creates_tp_history(tmp_path: Path) -> None:
    db = tmp_path / "cli-tools.db"
    conn = open_db(db)
    ensure_common_schema(conn)
    run_tool_migrations(conn, "teleport_test2", [mig_mod.MIGRATIONS[0]])
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='tp_history'"
    )
    assert cur.fetchone() is not None
    conn.close()


def test_v001_creates_index(tmp_path: Path) -> None:
    db = tmp_path / "cli-tools.db"
    conn = open_db(db)
    ensure_common_schema(conn)
    run_tool_migrations(conn, "teleport_test3", [mig_mod.MIGRATIONS[0]])
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_tp_alias_path'"
    )
    assert cur.fetchone() is not None
    conn.close()


def test_v001_idempotent(tmp_path: Path) -> None:
    db = tmp_path / "cli-tools.db"
    conn = open_db(db)
    ensure_common_schema(conn)
    # apply twice, should not raise
    run_tool_migrations(conn, "teleport_test4", [mig_mod.MIGRATIONS[0]])
    run_tool_migrations(conn, "teleport_test4", [mig_mod.MIGRATIONS[0]])
    conn.close()
