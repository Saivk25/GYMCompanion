"""Tests for app/application/workout/handlers/get_workout_handler.py."""

import pytest

from app.application.workout.handlers.get_workout_handler import GetWorkoutHandler
from app.application.workout.queries.get_workout import GetWorkoutQuery
from app.domain.user.identifiers import UserId
from app.domain.workout.identifiers import WorkoutId
from tests.application.workout.factories import (
    FakeUnitOfWork,
    FakeWorkoutRepository,
    a_planned_workout,
)


@pytest.mark.unit
def test_returns_a_workout_dto_for_an_existing_workout() -> None:
    workout = a_planned_workout()
    uow = FakeUnitOfWork(workouts=FakeWorkoutRepository({workout.id: workout}))
    handler = GetWorkoutHandler(uow=uow)

    result = handler.handle(GetWorkoutQuery(workout_id=workout.id, requester_id=workout.user_id))

    assert result.success is True
    assert result.value is not None
    assert result.value.workout_id == workout.id
    assert result.value.name == workout.name


@pytest.mark.unit
def test_a_missing_workout_is_reported_as_a_failed_result() -> None:
    uow = FakeUnitOfWork()
    handler = GetWorkoutHandler(uow=uow)
    missing_id = WorkoutId.generate()

    result = handler.handle(GetWorkoutQuery(workout_id=missing_id, requester_id=UserId.generate()))

    assert result.success is False
    assert str(missing_id) in result.errors[0]


@pytest.mark.unit
def test_a_non_owner_requester_is_denied() -> None:
    workout = a_planned_workout()
    uow = FakeUnitOfWork(workouts=FakeWorkoutRepository({workout.id: workout}))
    handler = GetWorkoutHandler(uow=uow)

    result = handler.handle(GetWorkoutQuery(workout_id=workout.id, requester_id=UserId.generate()))

    assert result.success is False
    assert result.forbidden is True
    assert result.value is None


@pytest.mark.unit
def test_never_commits_since_nothing_was_staged() -> None:
    workout = a_planned_workout()
    uow = FakeUnitOfWork(workouts=FakeWorkoutRepository({workout.id: workout}))
    handler = GetWorkoutHandler(uow=uow)

    handler.handle(GetWorkoutQuery(workout_id=workout.id, requester_id=workout.user_id))

    assert uow.committed is False


@pytest.mark.unit
def test_a_repository_get_failure_is_reported_as_a_failed_result() -> None:
    uow = FakeUnitOfWork(workouts=FakeWorkoutRepository(fail_on_get=True))
    handler = GetWorkoutHandler(uow=uow)

    result = handler.handle(
        GetWorkoutQuery(workout_id=WorkoutId.generate(), requester_id=UserId.generate())
    )

    assert result.success is False
