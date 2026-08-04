"""Tests for app/application/goal/queries/get_goal.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.application.goal.queries.get_goal import GetGoalQuery
from app.application.shared.query import Query
from app.domain.goal.identifiers import GoalId


@pytest.mark.unit
def test_get_goal_query_is_a_query() -> None:
    assert isinstance(GetGoalQuery(goal_id=GoalId.generate()), Query)


@pytest.mark.unit
def test_get_goal_query_exposes_its_goal_id() -> None:
    goal_id = GoalId.generate()
    query = GetGoalQuery(goal_id=goal_id)
    assert query.goal_id == goal_id


@pytest.mark.unit
def test_get_goal_query_is_immutable() -> None:
    query = GetGoalQuery(goal_id=GoalId.generate())
    with pytest.raises(FrozenInstanceError):
        query.goal_id = GoalId.generate()  # type: ignore[misc]
