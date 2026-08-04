"""Tests for app/application/goal/handlers/list_goals_handler.py."""

import pytest

from app.application.goal.handlers.list_goals_handler import ListGoalsHandler
from app.application.goal.queries.list_goals import ListGoalsQuery
from app.domain.user.identifiers import UserId
from tests.application.goal.factories import FakeGoalRepository, FakeUnitOfWork, a_created_goal


@pytest.mark.unit
def test_returns_every_goal_for_the_user_as_dtos() -> None:
    user_id = UserId.generate()
    mine_first = a_created_goal(user_id=user_id)
    mine_second = a_created_goal(user_id=user_id)
    someone_elses = a_created_goal()
    uow = FakeUnitOfWork(
        goals=FakeGoalRepository(
            {
                mine_first.id: mine_first,
                mine_second.id: mine_second,
                someone_elses.id: someone_elses,
            }
        )
    )
    handler = ListGoalsHandler(uow=uow)

    result = handler.handle(ListGoalsQuery(user_id=user_id))

    assert result.success is True
    assert result.value is not None
    returned_ids = {dto.goal_id for dto in result.value}
    assert returned_ids == {mine_first.id, mine_second.id}


@pytest.mark.unit
def test_returns_an_empty_tuple_for_a_user_with_no_goals() -> None:
    uow = FakeUnitOfWork()
    handler = ListGoalsHandler(uow=uow)

    result = handler.handle(ListGoalsQuery(user_id=UserId.generate()))

    assert result.success is True
    assert result.value == ()


@pytest.mark.unit
def test_never_commits_since_nothing_was_staged() -> None:
    uow = FakeUnitOfWork()
    handler = ListGoalsHandler(uow=uow)

    handler.handle(ListGoalsQuery(user_id=UserId.generate()))

    assert uow.committed is False


@pytest.mark.unit
def test_a_repository_list_failure_is_reported_as_a_failed_result() -> None:
    uow = FakeUnitOfWork(goals=FakeGoalRepository(fail_on_list=True))
    handler = ListGoalsHandler(uow=uow)

    result = handler.handle(ListGoalsQuery(user_id=UserId.generate()))

    assert result.success is False
