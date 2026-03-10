"""Unit tests for teleport action helpers (insert/get/update/delete)."""

# pylint: disable=import-outside-toplevel,missing-function-docstring

import sqlite3
from pathlib import Path

import pytest

from core_lib.common.db import ensure_common_schema, open_db, run_tool_migrations
from core_lib.teleport import migrations as mig_mod

pytestmark = pytest.mark.unit


def _prepare_conn(tmp_path: Path, tool_name: str = "teleport") -> sqlite3.Connection:
    db = tmp_path / "cli-tools.db"
    conn = open_db(db)
    ensure_common_schema(conn)
    run_tool_migrations(conn, tool_name, mig_mod.MIGRATIONS)
    return conn


def test_insert_and_get_alias(tmp_path: Path) -> None:
    from core_lib.teleport.actions import get_alias, insert_alias
    from core_lib.teleport.models import Alias

    conn = _prepare_conn(tmp_path)
    insert_alias(conn, "work", "/tmp")
    got = get_alias(conn, "work")
    assert isinstance(got, Alias)
    assert got is not None
    assert got.alias.lower() == "work"
    conn.close()


def test_get_alias_returns_none_when_absent(tmp_path: Path) -> None:
    from core_lib.teleport.actions import get_alias

    conn = _prepare_conn(tmp_path)
    assert get_alias(conn, "missing") is None
    conn.close()


def test_insert_alias_case_insensitive_unique(tmp_path: Path) -> None:
    from core_lib.teleport.actions import insert_alias

    conn = _prepare_conn(tmp_path)
    insert_alias(conn, "Work", "/tmp")
    with pytest.raises(sqlite3.IntegrityError):
        insert_alias(conn, "work", "/tmp2")
    conn.close()


def test_update_alias_path(tmp_path: Path) -> None:
    from core_lib.teleport.actions import get_alias, insert_alias, update_alias

    conn = _prepare_conn(tmp_path)
    insert_alias(conn, "w", "/tmp")
    update_alias(conn, "w", "/var")
    got = get_alias(conn, "w")
    assert got is not None
    assert got.path == "/var"
    conn.close()


def test_update_alias_updates_updated_at(tmp_path: Path) -> None:
    import time

    from core_lib.teleport.actions import get_alias, insert_alias, update_alias

    conn = _prepare_conn(tmp_path)
    insert_alias(conn, "w2", "/tmp")
    got_before = get_alias(conn, "w2")
    assert got_before is not None
    before = got_before.updated_at
    time.sleep(0.01)
    update_alias(conn, "w2", "/var")
    got_after = get_alias(conn, "w2")
    assert got_after is not None
    after = got_after.updated_at
    assert after >= before
    conn.close()


def test_delete_alias_removes_row(tmp_path: Path) -> None:
    from core_lib.teleport.actions import delete_alias, get_alias, insert_alias

    conn = _prepare_conn(tmp_path)
    insert_alias(conn, "d", "/tmp")
    delete_alias(conn, "d")
    assert get_alias(conn, "d") is None
    conn.close()


def test_delete_alias_sets_history_alias_id_null(tmp_path: Path) -> None:
    from core_lib.teleport.actions import delete_alias, insert_alias, insert_history

    conn = _prepare_conn(tmp_path)
    a = insert_alias(conn, "h", "/tmp")
    insert_history(conn, a.id, "/tmp", "pin")
    delete_alias(conn, "h")
    cur = conn.execute("SELECT alias_id FROM tp_history LIMIT 1")
    row = cur.fetchone()
    assert row is not None
    assert row[0] is None
    conn.close()


def test_list_aliases_empty(tmp_path: Path) -> None:
    from core_lib.teleport.actions import list_aliases

    conn = _prepare_conn(tmp_path)
    assert list_aliases(conn) == []
    conn.close()


def test_list_aliases_ordered_by_name(tmp_path: Path) -> None:
    from core_lib.teleport.actions import insert_alias, list_aliases

    conn = _prepare_conn(tmp_path)
    insert_alias(conn, "b", "/b")
    insert_alias(conn, "a", "/a")
    names = [a.alias for a in list_aliases(conn)]
    assert [n.lower() for n in names] == sorted([n.lower() for n in names])
    conn.close()


def test_list_aliases_returns_all(tmp_path: Path) -> None:
    from core_lib.teleport.actions import insert_alias, list_aliases

    conn = _prepare_conn(tmp_path)
    insert_alias(conn, "one", "/1")
    insert_alias(conn, "two", "/2")
    assert len(list_aliases(conn)) >= 2
    conn.close()


def test_increment_visit_count(tmp_path: Path) -> None:
    from core_lib.teleport.actions import get_alias, increment_visit_count, insert_alias

    conn = _prepare_conn(tmp_path)
    a = insert_alias(conn, "v", "/tmp")
    assert a.id is not None
    increment_visit_count(conn, a.id)
    got1 = get_alias(conn, "v")
    assert got1 is not None
    assert got1.visit_count == 1
    increment_visit_count(conn, a.id)
    got2 = get_alias(conn, "v")
    assert got2 is not None
    assert got2.visit_count == 2
    conn.close()


def test_insert_history_row(tmp_path: Path) -> None:
    from core_lib.teleport.actions import insert_history

    conn = _prepare_conn(tmp_path)
    insert_history(conn, None, "/tmp", "pin")
    cur = conn.execute("SELECT action, path FROM tp_history ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    assert row[0] == "pin"
    conn.close()


def test_prune_history_keeps_1000_rows(tmp_path: Path) -> None:
    from core_lib.teleport.actions import insert_history, prune_history

    conn = _prepare_conn(tmp_path)
    for i in range(1001):
        insert_history(conn, None, f"/tmp/{i}", "jump")
    prune_history(conn, limit=1000)
    cur = conn.execute("SELECT COUNT(*) FROM tp_history")
    assert cur.fetchone()[0] == 1000
    conn.close()


def test_prune_history_keeps_newest(tmp_path: Path) -> None:
    from core_lib.teleport.actions import insert_history, prune_history

    conn = _prepare_conn(tmp_path)
    for i in range(3):
        insert_history(conn, None, f"/tmp/{i}", "jump")
    prune_history(conn, limit=2)
    cur = conn.execute("SELECT path FROM tp_history ORDER BY id ASC")
    rows = [r[0] for r in cur.fetchall()]
    assert rows == ["/tmp/1", "/tmp/2"]
    conn.close()


def test_prune_history_noop_below_limit(tmp_path: Path) -> None:
    from core_lib.teleport.actions import insert_history, prune_history

    conn = _prepare_conn(tmp_path)
    for i in range(5):
        insert_history(conn, None, f"/tmp/{i}", "jump")
    prune_history(conn, limit=1000)
    cur = conn.execute("SELECT COUNT(*) FROM tp_history")
    assert cur.fetchone()[0] == 5
    conn.close()
