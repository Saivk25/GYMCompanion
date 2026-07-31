"""Tests for app/application/workout/handlers/list_workouts_handler.py."""

import pytest

from app.application.workout.handlers.list_workouts_handler import ListWorkoutsHandler
from app.application.workout.queries.list_workouts import ListWorkoutsQuery
from app.domain.user.identifiers import UserId
from tests.application.workout.factories import (
    FakeUnitOfWork,
    FakeWorkoutRepository,
    a_planned_workout,
)


@pytest.mark.unit
def test_returns_every_workout_for_the_user_as_dtos() -> None:
    user_id = UserId.generate()
    mine_first = a_planned_workout(user_id=user_id)
    mine_second = a_planned_workout(user_id=user_id)
    someone_elses = a_planned_workout()
    uow = FakeUnitOfWork(
        workouts=FakeWorkoutRepository(
            {
                mine_first.id: mine_first,
                mine_second.id: mine_second,
                someone_elses.id: someone_elses,
            }
        )
    )
    handler = ListWorkoutsHandler(uow=uow)

    result = handler.handle(ListWorkoutsQuery(user_id=user_id))

    assert result.success is True
    assert result.value is not None
    returned_ids = {dto.workout_id for dto in result.value}
    assert returned_ids == {mine_first.id, mine_second.id}


@pytest.mark.unit
def test_returns_an_empty_tuple_for_a_user_with_no_workouts() -> None:
    uow = FakeUnitOfWork()
    handler = ListWorkoutsHandler(uow=uow)

    result = handler.handle(ListWorkoutsQuery(user_id=UserId.generate()))

    assert result.success is True
    assert result.value == ()


@pytest.mark.unit
def test_never_commits_since_nothing_was_staged() -> None:
    uow = FakeUnitOfWork()
    handler = ListWorkoutsHandler(uow=uow)

    handler.handle(ListWorkoutsQuery(user_id=UserId.generate()))

    assert uow.committed is False


@pytest.mark.unit
def test_a_repository_list_failure_is_reported_as_a_failed_result() -> None:
    uow = FakeUnitOfWork(workouts=FakeWorkoutRepository(fail_on_list=True))
    handler = ListWorkoutsHandler(uow=uow)

    result = handler.handle(ListWorkoutsQuery(user_id=UserId.generate()))

    assert result.success is False
