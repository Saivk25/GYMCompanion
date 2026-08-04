"""Tests for app/application/goal/handlers/get_goal_handler.py."""

import pytest

from app.application.goal.handlers.get_goal_handler import GetGoalHandler
from app.application.goal.queries.get_goal import GetGoalQuery
from app.domain.goal.identifiers import GoalId
from tests.application.goal.factories import FakeGoalRepository, FakeUnitOfWork, a_created_goal


@pytest.mark.unit
def test_returns_a_goal_dto_for_an_existing_goal() -> None:
    goal = a_created_goal()
    uow = FakeUnitOfWork(goals=FakeGoalRepository({goal.id: goal}))
    handler = GetGoalHandler(uow=uow)

    result = handler.handle(GetGoalQuery(goal_id=goal.id))

    assert result.success is True
    assert result.value is not None
    assert result.value.goal_id == goal.id
    assert result.value.user_id == goal.user_id


@pytest.mark.unit
def test_a_missing_goal_is_reported_as_a_failed_result() -> None:
    uow = FakeUnitOfWork()
    handler = GetGoalHandler(uow=uow)
    missing_id = GoalId.generate()

    result = handler.handle(GetGoalQuery(goal_id=missing_id))

    assert result.success is False
    assert str(missing_id) in result.errors[0]


@pytest.mark.unit
def test_never_commits_since_nothing_was_staged() -> None:
    goal = a_created_goal()
    uow = FakeUnitOfWork(goals=FakeGoalRepository({goal.id: goal}))
    handler = GetGoalHandler(uow=uow)

    handler.handle(GetGoalQuery(goal_id=goal.id))

    assert uow.committed is False


@pytest.mark.unit
def test_a_repository_get_failure_is_reported_as_a_failed_result() -> None:
    uow = FakeUnitOfWork(goals=FakeGoalRepository(fail_on_get=True))
    handler = GetGoalHandler(uow=uow)

    result = handler.handle(GetGoalQuery(goal_id=GoalId.generate()))

    assert result.success is False
