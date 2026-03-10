"""Unit tests for Teleport Pydantic models."""

# pylint: disable=import-outside-toplevel,missing-function-docstring

from datetime import UTC, datetime
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def test_alias_valid_construction() -> None:
    from core_lib.teleport.models import Alias

    a = Alias(
        id=1,
        alias="work",
        path=str(Path("/tmp")),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    assert a.alias == "work"


def test_alias_path_rejects_newline() -> None:
    from pydantic import ValidationError

    from core_lib.teleport.models import Alias

    with pytest.raises(ValidationError):
        Alias(
            id=1,
            alias="x",
            path="foo\nbar",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )


def test_alias_path_rejects_carriage_return() -> None:
    from pydantic import ValidationError

    from core_lib.teleport.models import Alias

    with pytest.raises(ValidationError):
        Alias(
            id=1,
            alias="x",
            path="foo\rbar",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )


def test_alias_as_path_returns_path_object() -> None:
    from core_lib.teleport.models import Alias
    P = Path

    a = Alias(
        id=1,
        alias="w",
        path=str(P("/tmp")),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    assert a.as_path() == P(a.path)


def test_alias_model_validate_from_dict() -> None:
    from core_lib.teleport.models import Alias
    # use top-level `datetime` import from module header

    d = {
        "id": None,
        "alias": "x",
        "path": "/tmp",
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    a = Alias.model_validate(d)
    assert a.alias == "x"


def test_alias_visit_count_defaults_to_zero() -> None:
    from core_lib.teleport.models import Alias

    a = Alias(
        id=None,
        alias="x",
        path="/tmp",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    assert a.visit_count == 0


def test_history_entry_valid_construction() -> None:
    from core_lib.teleport.models import HistoryEntry

    h = HistoryEntry(
        id=None,
        alias_id=None,
        path="/tmp",
        action="jump",
        occurred_at=datetime.now(UTC),
    )
    assert h.action == "jump"


def test_history_entry_action_values() -> None:
    from core_lib.teleport.models import HistoryEntry

    for act in ("jump", "pin", "unpin"):
        HistoryEntry(
            id=None,
            alias_id=None,
            path="/tmp",
            action=act,
            occurred_at=datetime.now(UTC),
        )
