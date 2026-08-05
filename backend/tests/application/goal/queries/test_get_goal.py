"""Tests for app/application/goal/queries/get_goal.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.application.goal.queries.get_goal import GetGoalQuery
from app.application.shared.query import Query
from app.domain.goal.identifiers import GoalId
from app.domain.user.identifiers import UserId


@pytest.mark.unit
def test_get_goal_query_is_a_query() -> None:
    assert isinstance(
        GetGoalQuery(goal_id=GoalId.generate(), requester_id=UserId.generate()), Query
    )


@pytest.mark.unit
def test_get_goal_query_exposes_its_goal_id() -> None:
    goal_id = GoalId.generate()
    query = GetGoalQuery(goal_id=goal_id, requester_id=UserId.generate())
    assert query.goal_id == goal_id


@pytest.mark.unit
def test_get_goal_query_is_immutable() -> None:
    query = GetGoalQuery(goal_id=GoalId.generate(), requester_id=UserId.generate())
    with pytest.raises(FrozenInstanceError):
        query.goal_id = GoalId.generate()  # type: ignore[misc]
