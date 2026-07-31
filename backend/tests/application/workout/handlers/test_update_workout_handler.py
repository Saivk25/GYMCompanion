"""Tests for app/application/workout/handlers/update_workout_handler.py."""

from datetime import timedelta

import pytest

from app.application.workout.commands.update_workout import UpdateWorkoutCommand
from app.application.workout.handlers.update_workout_handler import UpdateWorkoutHandler
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.workout.identifiers import WorkoutId
from app.domain.workout.value_objects import WorkoutDuration, WorkoutGoal, WorkoutNotes
from tests.application.workout.factories import (
    FakeUnitOfWork,
    FakeWorkoutRepository,
    OrderTrackingDispatcher,
    OrderTrackingUnitOfWork,
    RecordingDispatcher,
    a_fixed_clock,
    a_planned_workout,
)


@pytest.mark.unit
def test_replaces_goal_and_notes_and_returns_the_workout_id() -> None:
    workout = a_planned_workout()
    uow = FakeUnitOfWork(workouts=FakeWorkoutRepository({workout.id: workout}))
    handler = UpdateWorkoutHandler(uow=uow, dispatcher=RecordingDispatcher())

    result = handler.handle(
        UpdateWorkoutCommand(
            workout_id=workout.id,
            goal=WorkoutGoal("hypertrophy"),
            notes=WorkoutNotes("felt good"),
        )
    )

    assert result.success is True
    assert result.value == workout.id
    assert workout.goal == WorkoutGoal("hypertrophy")
    assert workout.notes == WorkoutNotes("felt good")


@pytest.mark.unit
def test_can_clear_goal_and_notes_with_none() -> None:
    workout = a_planned_workout()
    workout.update_goal(WorkoutGoal("strength"))
    uow = FakeUnitOfWork(workouts=FakeWorkoutRepository({workout.id: workout}))
    handler = UpdateWorkoutHandler(uow=uow, dispatcher=RecordingDispatcher())

    handler.handle(UpdateWorkoutCommand(workout_id=workout.id, goal=None, notes=None))

    assert workout.goal is None
    assert workout.notes is None


@pytest.mark.unit
def test_commits_and_dispatches_no_events_since_none_are_raised() -> None:
    workout = a_planned_workout()
    uow = FakeUnitOfWork(workouts=FakeWorkoutRepository({workout.id: workout}))
    dispatcher = RecordingDispatcher()
    handler = UpdateWorkoutHandler(uow=uow, dispatcher=dispatcher)

    handler.handle(UpdateWorkoutCommand(workout_id=workout.id, goal=None, notes=None))

    assert uow.committed is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_dispatch_happens_strictly_after_commit() -> None:
    workout = a_planned_workout()
    call_order: list[str] = []
    uow = OrderTrackingUnitOfWork(
        workouts=FakeWorkoutRepository({workout.id: workout}), call_order=call_order
    )
    dispatcher = OrderTrackingDispatcher(call_order)
    handler = UpdateWorkoutHandler(uow=uow, dispatcher=dispatcher)

    handler.handle(UpdateWorkoutCommand(workout_id=workout.id, goal=None, notes=None))

    assert call_order == ["commit", "dispatch"]


@pytest.mark.unit
def test_a_missing_workout_is_reported_as_a_failed_result_and_rolls_back() -> None:
    uow = FakeUnitOfWork()
    dispatcher = RecordingDispatcher()
    handler = UpdateWorkoutHandler(uow=uow, dispatcher=dispatcher)
    missing_id = WorkoutId.generate()

    result = handler.handle(UpdateWorkoutCommand(workout_id=missing_id, goal=None, notes=None))

    assert result.success is False
    assert str(missing_id) in result.errors[0]
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_repository_get_failure_is_reported_as_a_failed_result_and_rolls_back() -> None:
    uow = FakeUnitOfWork(workouts=FakeWorkoutRepository(fail_on_get=True))
    dispatcher = RecordingDispatcher()
    handler = UpdateWorkoutHandler(uow=uow, dispatcher=dispatcher)

    result = handler.handle(
        UpdateWorkoutCommand(workout_id=WorkoutId.generate(), goal=None, notes=None)
    )

    assert result.success is False
    assert uow.rolled_back is True


@pytest.mark.unit
def test_a_commit_failure_is_reported_as_a_failed_result_and_rolls_back() -> None:
    workout = a_planned_workout()
    uow = FakeUnitOfWork(workouts=FakeWorkoutRepository({workout.id: workout}), fail_on_commit=True)
    dispatcher = RecordingDispatcher()
    handler = UpdateWorkoutHandler(uow=uow, dispatcher=dispatcher)

    result = handler.handle(UpdateWorkoutCommand(workout_id=workout.id, goal=None, notes=None))

    assert result.success is False
    assert uow.rolled_back is True


@pytest.mark.unit
def test_updating_a_completed_workout_raises_and_still_rolls_back() -> None:
    workout = a_planned_workout()
    workout.start(clock=a_fixed_clock())
    workout.complete(duration=WorkoutDuration(timedelta(minutes=30)), clock=a_fixed_clock())
    workout.pull_domain_events()
    uow = FakeUnitOfWork(workouts=FakeWorkoutRepository({workout.id: workout}))
    dispatcher = RecordingDispatcher()
    handler = UpdateWorkoutHandler(uow=uow, dispatcher=dispatcher)

    with pytest.raises(DomainInvariantViolationError, match="cannot modify"):
        handler.handle(UpdateWorkoutCommand(workout_id=workout.id, goal=None, notes=None))

    assert dispatcher.dispatched == []
