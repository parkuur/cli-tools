"""Unit tests for the TeleportService abstraction."""

# pylint: disable=import-outside-toplevel,missing-function-docstring

from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def test_pin_stores_alias(tmp_path: Path) -> None:
    from core_lib.teleport.service import TeleportService

    svc = TeleportService(tmp_path / "cli-tools.db")
    svc.pin("work", Path("/tmp"))
    found = svc.show("work")
    assert len(found) == 1
    assert found[0].alias.lower() == "work"


def test_pin_resolves_path(tmp_path: Path) -> None:
    from core_lib.teleport.service import TeleportService

    svc = TeleportService(tmp_path / "cli-tools.db")
    alias = svc.pin("r", Path("."))
    assert alias.path.startswith(str(Path.cwd()).rstrip("/") ) or alias.path.startswith("/")


def test_pin_raises_conflict_on_duplicate(tmp_path: Path) -> None:
    from core_lib.common.exceptions import AliasConflictError
    from core_lib.teleport.service import TeleportService

    svc = TeleportService(tmp_path / "cli-tools.db")
    svc.pin("dup", Path("/tmp"))
    with pytest.raises(AliasConflictError):
        svc.pin("dup", Path("/tmp"))


def test_pin_overwrite_replaces_path(tmp_path: Path) -> None:
    from core_lib.teleport.service import TeleportService

    svc = TeleportService(tmp_path / "cli-tools.db")
    target_a = tmp_path / "a"
    target_b = tmp_path / "b"
    svc.pin("o", target_a)
    svc.pin("o", target_b, overwrite=True)
    assert svc.show("o")[0].path == str(target_b.resolve())


def test_pin_warns_nonexistent_path(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    from core_lib.teleport.service import TeleportService

    svc = TeleportService(tmp_path / "cli-tools.db")
    svc.pin("nx", Path("/this/path/should/not/exist"))
    assert "WARNING" in caplog.text


def test_pin_raises_invalid_path_on_newline(tmp_path: Path) -> None:
    from core_lib.common.exceptions import InvalidPathError
    from core_lib.teleport.service import TeleportService

    svc = TeleportService(tmp_path / "cli-tools.db")
    with pytest.raises(InvalidPathError):
        svc.pin("bad", Path("/tmp\nfoo"))


def test_pin_returns_alias_model(tmp_path: Path) -> None:
    from core_lib.teleport.models import Alias
    from core_lib.teleport.service import TeleportService

    svc = TeleportService(tmp_path / "cli-tools.db")
    a = svc.pin("m", Path("/tmp"))
    assert isinstance(a, Alias)


def test_unpin_removes_alias(tmp_path: Path) -> None:
    from core_lib.teleport.service import TeleportService

    svc = TeleportService(tmp_path / "cli-tools.db")
    svc.pin("u", Path("/tmp"))
    svc.unpin("u")
    assert svc.list_aliases() == []


def test_unpin_raises_not_found(tmp_path: Path) -> None:
    from core_lib.common.exceptions import AliasNotFoundError
    from core_lib.teleport.service import TeleportService

    svc = TeleportService(tmp_path / "cli-tools.db")
    with pytest.raises(AliasNotFoundError):
        svc.unpin("missing")


def test_resolve_returns_path(tmp_path: Path) -> None:
    from core_lib.teleport.service import TeleportService

    svc = TeleportService(tmp_path / "cli-tools.db")
    svc.pin("rp", Path("/tmp"))
    p = svc.resolve("rp", Path("/from"))
    assert p is not None


def test_resolve_returns_none_for_unknown(tmp_path: Path) -> None:
    from core_lib.teleport.service import TeleportService

    svc = TeleportService(tmp_path / "cli-tools.db")
    assert svc.resolve("nope", Path("/from")) is None


def test_resolve_increments_visit_count(tmp_path: Path) -> None:
    from core_lib.teleport.service import TeleportService

    svc = TeleportService(tmp_path / "cli-tools.db")
    svc.pin("vc", Path("/tmp"))
    svc.resolve("vc", Path("/from1"))
    svc.resolve("vc", Path("/from2"))
    assert svc.show("vc")[0].visit_count == 2


def test_resolve_records_jump_history(tmp_path: Path) -> None:
    from core_lib.common.db import open_db
    from core_lib.teleport.service import TeleportService

    svc = TeleportService(tmp_path / "cli-tools.db")
    svc.pin("jh", Path("/tmp"))
    svc.resolve("jh", Path("/from"))
    conn = open_db(tmp_path / "cli-tools.db")
    cur = conn.execute("SELECT action FROM tp_history ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    assert row is not None and row[0] == "jump"
    conn.close()


def test_resolve_stores_previous_path(tmp_path: Path) -> None:
    from core_lib.teleport.service import TeleportService

    svc = TeleportService(tmp_path / "cli-tools.db")
    svc.pin("pr", Path("/tmp"))
    svc.resolve("pr", Path("/from"))
    assert svc.previous() == Path("/from")


def test_resolve_previous_path_updates_on_each_jump(tmp_path: Path) -> None:
    from core_lib.teleport.service import TeleportService

    svc = TeleportService(tmp_path / "cli-tools.db")
    svc.pin("p1", Path("/tmp"))
    svc.resolve("p1", Path("/from1"))
    svc.resolve("p1", Path("/from2"))
    assert svc.previous() == Path("/from2")


def test_previous_returns_none_initially(tmp_path: Path) -> None:
    from core_lib.teleport.service import TeleportService

    svc = TeleportService(tmp_path / "cli-tools.db")
    assert svc.previous() is None


def test_previous_returns_last_cwd(tmp_path: Path) -> None:
    from core_lib.teleport.service import TeleportService

    svc = TeleportService(tmp_path / "cli-tools.db")
    svc.pin("pp", Path("/tmp"))
    svc.resolve("pp", Path("/from"))
    assert svc.previous() == Path("/from")


def test_list_aliases_empty(tmp_path: Path) -> None:
    from core_lib.teleport.service import TeleportService

    svc = TeleportService(tmp_path / "cli-tools.db")
    assert svc.list_aliases() == []


def test_list_aliases_sorted(tmp_path: Path) -> None:
    from core_lib.teleport.service import TeleportService

    svc = TeleportService(tmp_path / "cli-tools.db")
    svc.pin("b", Path("/b"))
    svc.pin("a", Path("/a"))
    names = [a.alias for a in svc.list_aliases()]
    assert [n.lower() for n in names] == sorted([n.lower() for n in names])


def test_show_single_alias(tmp_path: Path) -> None:
    from core_lib.teleport.service import TeleportService

    svc = TeleportService(tmp_path / "cli-tools.db")
    svc.pin("s", Path("/tmp"))
    res = svc.show("s")
    assert len(res) == 1


def test_show_all_aliases(tmp_path: Path) -> None:
    from core_lib.teleport.service import TeleportService

    svc = TeleportService(tmp_path / "cli-tools.db")
    svc.pin("x", Path("/x"))
    svc.pin("y", Path("/y"))
    assert len(svc.show()) >= 2


def test_show_raises_not_found(tmp_path: Path) -> None:
    from core_lib.common.exceptions import AliasNotFoundError
    from core_lib.teleport.service import TeleportService

    svc = TeleportService(tmp_path / "cli-tools.db")
    with pytest.raises(AliasNotFoundError):
        svc.show("missing")


def test_show_does_not_record_history(tmp_path: Path) -> None:
    from core_lib.common.db import open_db
    from core_lib.teleport.service import TeleportService

    svc = TeleportService(tmp_path / "cli-tools.db")
    svc.pin("sh", Path("/tmp"))
    svc.show("sh")
    conn = open_db(tmp_path / "cli-tools.db")
    cur = conn.execute("SELECT COUNT(*) FROM tp_history")
    assert cur.fetchone()[0] == 0
    conn.close()


def test_service_init_creates_schema(tmp_path: Path) -> None:
    from core_lib.common.db import open_db
    from core_lib.teleport.service import TeleportService

    db = tmp_path / "cli-tools.db"
    TeleportService(db)
    conn = open_db(db)
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tp_aliases'")
    assert cur.fetchone() is not None
    conn.close()


def test_service_init_idempotent(tmp_path: Path) -> None:
    from core_lib.teleport.service import TeleportService

    db = tmp_path / "cli-tools.db"
    TeleportService(db)
    TeleportService(db)
