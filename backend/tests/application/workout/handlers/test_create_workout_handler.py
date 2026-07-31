"""Tests for app/application/workout/handlers/create_workout_handler.py."""

from datetime import date

import pytest

from app.application.workout.commands.create_workout import CreateWorkoutCommand
from app.application.workout.handlers.create_workout_handler import CreateWorkoutHandler
from app.domain.user.identifiers import UserId
from app.domain.workout.events import WorkoutPlanned
from app.domain.workout.value_objects import WorkoutDate, WorkoutName
from tests.application.workout.factories import (
    FakeUnitOfWork,
    FakeUserRepository,
    FakeWorkoutRepository,
    OrderTrackingDispatcher,
    OrderTrackingUnitOfWork,
    RecordingDispatcher,
    a_fixed_clock,
    a_registered_user,
)


def _a_command_for(user_id: UserId) -> CreateWorkoutCommand:
    return CreateWorkoutCommand(
        user_id=user_id, name=WorkoutName("Push Day"), planned_date=WorkoutDate(date(2026, 1, 1))
    )


@pytest.mark.unit
def test_plans_a_new_workout_and_returns_its_id() -> None:
    user = a_registered_user()
    uow = FakeUnitOfWork(users=FakeUserRepository({user.id: user}))
    handler = CreateWorkoutHandler(uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock())

    result = handler.handle(_a_command_for(user.id))

    assert result.success is True
    assert result.value is not None
    assert uow.workouts.get(result.value) is not None
    assert uow.workouts.get(result.value).name == WorkoutName("Push Day")  # type: ignore[union-attr]


@pytest.mark.unit
def test_commits_the_unit_of_work() -> None:
    user = a_registered_user()
    uow = FakeUnitOfWork(users=FakeUserRepository({user.id: user}))
    handler = CreateWorkoutHandler(uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock())

    handler.handle(_a_command_for(user.id))

    assert uow.committed is True
    assert uow.rolled_back is False


@pytest.mark.unit
def test_dispatches_workout_planned_after_commit() -> None:
    user = a_registered_user()
    uow = FakeUnitOfWork(users=FakeUserRepository({user.id: user}))
    dispatcher = RecordingDispatcher()
    handler = CreateWorkoutHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(_a_command_for(user.id))

    assert len(dispatcher.dispatched) == 1
    event = dispatcher.dispatched[0]
    assert isinstance(event, WorkoutPlanned)
    assert event.workout_id == result.value


@pytest.mark.unit
def test_dispatch_happens_strictly_after_commit() -> None:
    user = a_registered_user()
    call_order: list[str] = []
    uow = OrderTrackingUnitOfWork(users=FakeUserRepository({user.id: user}), call_order=call_order)
    dispatcher = OrderTrackingDispatcher(call_order)
    handler = CreateWorkoutHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    handler.handle(_a_command_for(user.id))

    assert call_order == ["commit", "dispatch"]


@pytest.mark.unit
def test_a_missing_user_is_reported_as_a_failed_result_and_rolls_back() -> None:
    uow = FakeUnitOfWork()
    dispatcher = RecordingDispatcher()
    handler = CreateWorkoutHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(_a_command_for(a_registered_user().id))

    assert result.success is False
    assert "not found" in result.errors[0]
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_workout_repository_add_failure_is_reported_as_a_failed_result() -> None:
    user = a_registered_user()
    uow = FakeUnitOfWork(
        users=FakeUserRepository({user.id: user}),
        workouts=FakeWorkoutRepository(fail_on_add=True),
    )
    handler = CreateWorkoutHandler(uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock())

    result = handler.handle(_a_command_for(user.id))

    assert result.success is False
    assert "already exists" in result.errors[0]


@pytest.mark.unit
def test_a_commit_failure_is_reported_as_a_failed_result_and_rolls_back() -> None:
    user = a_registered_user()
    uow = FakeUnitOfWork(users=FakeUserRepository({user.id: user}), fail_on_commit=True)
    dispatcher = RecordingDispatcher()
    handler = CreateWorkoutHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(_a_command_for(user.id))

    assert result.success is False
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_user_repository_get_failure_is_reported_as_a_failed_result() -> None:
    uow = FakeUnitOfWork(users=FakeUserRepository(fail_on_get=True))
    handler = CreateWorkoutHandler(uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock())

    result = handler.handle(_a_command_for(a_registered_user().id))

    assert result.success is False


@pytest.mark.unit
def test_generates_a_distinct_workout_id_each_call() -> None:
    user = a_registered_user()
    uow = FakeUnitOfWork(users=FakeUserRepository({user.id: user}))
    handler = CreateWorkoutHandler(uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock())

    first = handler.handle(_a_command_for(user.id))
    second = handler.handle(_a_command_for(user.id))

    assert first.value != second.value
