"""Unit tests for metadata management helpers."""

# pylint: disable=import-outside-toplevel,missing-function-docstring

from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def test_get_metadata_returns_none_when_absent(tmp_db_path: Path) -> None:
    from core_lib.common.db import ensure_common_schema, open_db
    from core_lib.common.metadata import get_metadata

    conn = open_db(tmp_db_path)
    ensure_common_schema(conn)
    assert get_metadata(conn, "tp", "missing") is None
    conn.close()


def test_set_and_get_metadata_roundtrip(tmp_db_path: Path) -> None:
    from core_lib.common.db import ensure_common_schema, open_db
    from core_lib.common.metadata import get_metadata, set_metadata

    conn = open_db(tmp_db_path)
    ensure_common_schema(conn)
    set_metadata(conn, "tp", "k", "v")
    assert get_metadata(conn, "tp", "k") == "v"
    conn.close()


def test_set_metadata_upserts(tmp_db_path: Path) -> None:
    from core_lib.common.db import ensure_common_schema, open_db
    from core_lib.common.metadata import get_metadata, set_metadata

    conn = open_db(tmp_db_path)
    ensure_common_schema(conn)
    set_metadata(conn, "tp", "k", "v1")
    set_metadata(conn, "tp", "k", "v2")
    assert get_metadata(conn, "tp", "k") == "v2"
    conn.close()


def test_metadata_namespaced_by_tool(tmp_db_path: Path) -> None:
    from core_lib.common.db import ensure_common_schema, open_db
    from core_lib.common.metadata import get_metadata, set_metadata

    conn = open_db(tmp_db_path)
    ensure_common_schema(conn)
    set_metadata(conn, "tp", "k", "v1")
    set_metadata(conn, "bm", "k", "v2")
    assert get_metadata(conn, "tp", "k") == "v1"
    assert get_metadata(conn, "bm", "k") == "v2"
    conn.close()


def test_metadata_value_can_be_empty_string(tmp_db_path: Path) -> None:
    from core_lib.common.db import ensure_common_schema, open_db
    from core_lib.common.metadata import get_metadata, set_metadata

    conn = open_db(tmp_db_path)
    ensure_common_schema(conn)
    set_metadata(conn, "tp", "k", "")
    assert get_metadata(conn, "tp", "k") == ""
    conn.close()
