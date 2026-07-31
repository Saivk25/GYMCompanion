"""Tests for app/application/shared/query.py."""

from dataclasses import FrozenInstanceError, dataclass

import pytest

from app.application.shared.query import Query


@pytest.mark.unit
def test_query_can_be_instantiated_directly() -> None:
    query = Query()
    assert isinstance(query, Query)


@pytest.mark.unit
def test_query_is_immutable() -> None:
    query = Query()
    with pytest.raises(FrozenInstanceError):
        query.anything = 1  # type: ignore[attr-defined]


@pytest.mark.unit
def test_a_subclass_forgetting_frozen_true_fails_at_class_definition_time() -> None:
    with pytest.raises(TypeError):

        @dataclass
        class _NotFrozen(Query):  # type: ignore[misc]
            value: int = 0


@pytest.mark.unit
def test_a_well_formed_subclass_carries_its_own_fields() -> None:
    @dataclass(frozen=True, kw_only=True)
    class _GetActiveGoalQuery(Query):
        user_id: str

    query = _GetActiveGoalQuery(user_id="abc-123")
    assert query.user_id == "abc-123"
    assert isinstance(query, Query)
