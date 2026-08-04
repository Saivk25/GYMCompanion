"""Tests for app/application/goal/queries/list_goals.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.application.goal.queries.list_goals import ListGoalsQuery
from app.application.shared.query import Query
from app.domain.user.identifiers import UserId


@pytest.mark.unit
def test_list_goals_query_is_a_query() -> None:
    assert isinstance(ListGoalsQuery(user_id=UserId.generate()), Query)


@pytest.mark.unit
def test_list_goals_query_exposes_its_user_id() -> None:
    user_id = UserId.generate()
    query = ListGoalsQuery(user_id=user_id)
    assert query.user_id == user_id


@pytest.mark.unit
def test_list_goals_query_is_immutable() -> None:
    query = ListGoalsQuery(user_id=UserId.generate())
    with pytest.raises(FrozenInstanceError):
        query.user_id = UserId.generate()  # type: ignore[misc]
