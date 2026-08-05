"""Tests for app/application/workout/handlers/cancel_workout_handler.py."""

from datetime import timedelta

import pytest

from app.application.workout.commands.cancel_workout import CancelWorkoutCommand
from app.application.workout.handlers.cancel_workout_handler import CancelWorkoutHandler
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.user.identifiers import UserId
from app.domain.workout.enums import WorkoutStatus
from app.domain.workout.identifiers import WorkoutId
from app.domain.workout.value_objects import WorkoutDuration
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
def test_cancels_the_workout_and_returns_its_id() -> None:
    workout = a_planned_workout()
    uow = FakeUnitOfWork(workouts=FakeWorkoutRepository({workout.id: workout}))
    handler = CancelWorkoutHandler(uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock())

    result = handler.handle(
        CancelWorkoutCommand(workout_id=workout.id, requester_id=workout.user_id)
    )

    assert result.success is True
    assert result.value == workout.id
    assert workout.status == WorkoutStatus.CANCELLED


@pytest.mark.unit
def test_commits_and_dispatches_after_commit() -> None:
    workout = a_planned_workout()
    uow = FakeUnitOfWork(workouts=FakeWorkoutRepository({workout.id: workout}))
    dispatcher = RecordingDispatcher()
    handler = CancelWorkoutHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    handler.handle(CancelWorkoutCommand(workout_id=workout.id, requester_id=workout.user_id))

    assert uow.committed is True
    assert len(dispatcher.dispatched) == 1


@pytest.mark.unit
def test_dispatch_happens_strictly_after_commit() -> None:
    workout = a_planned_workout()
    call_order: list[str] = []
    uow = OrderTrackingUnitOfWork(
        workouts=FakeWorkoutRepository({workout.id: workout}), call_order=call_order
    )
    dispatcher = OrderTrackingDispatcher(call_order)
    handler = CancelWorkoutHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    handler.handle(CancelWorkoutCommand(workout_id=workout.id, requester_id=workout.user_id))

    assert call_order == ["commit", "dispatch"]


@pytest.mark.unit
def test_a_missing_workout_is_reported_as_a_failed_result_and_rolls_back() -> None:
    uow = FakeUnitOfWork()
    dispatcher = RecordingDispatcher()
    handler = CancelWorkoutHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())
    missing_id = WorkoutId.generate()

    result = handler.handle(
        CancelWorkoutCommand(workout_id=missing_id, requester_id=UserId.generate())
    )

    assert result.success is False
    assert str(missing_id) in result.errors[0]
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_non_owner_requester_is_denied_and_rolls_back() -> None:
    workout = a_planned_workout()
    uow = FakeUnitOfWork(workouts=FakeWorkoutRepository({workout.id: workout}))
    dispatcher = RecordingDispatcher()
    handler = CancelWorkoutHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(
        CancelWorkoutCommand(workout_id=workout.id, requester_id=UserId.generate())
    )

    assert result.success is False
    assert result.forbidden is True
    assert result.value is None
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_repository_get_failure_is_reported_as_a_failed_result_and_rolls_back() -> None:
    uow = FakeUnitOfWork(workouts=FakeWorkoutRepository(fail_on_get=True))
    dispatcher = RecordingDispatcher()
    handler = CancelWorkoutHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(
        CancelWorkoutCommand(workout_id=WorkoutId.generate(), requester_id=UserId.generate())
    )

    assert result.success is False
    assert uow.rolled_back is True


@pytest.mark.unit
def test_a_commit_failure_is_reported_as_a_failed_result_and_rolls_back() -> None:
    workout = a_planned_workout()
    uow = FakeUnitOfWork(workouts=FakeWorkoutRepository({workout.id: workout}), fail_on_commit=True)
    dispatcher = RecordingDispatcher()
    handler = CancelWorkoutHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(
        CancelWorkoutCommand(workout_id=workout.id, requester_id=workout.user_id)
    )

    assert result.success is False
    assert uow.rolled_back is True


@pytest.mark.unit
def test_cancelling_a_completed_workout_raises_and_still_rolls_back() -> None:
    workout = a_planned_workout()
    workout.start(clock=a_fixed_clock())
    workout.complete(duration=WorkoutDuration(timedelta(minutes=30)), clock=a_fixed_clock())
    workout.pull_domain_events()
    uow = FakeUnitOfWork(workouts=FakeWorkoutRepository({workout.id: workout}))
    dispatcher = RecordingDispatcher()
    handler = CancelWorkoutHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    with pytest.raises(DomainInvariantViolationError, match="cannot transition"):
        handler.handle(CancelWorkoutCommand(workout_id=workout.id, requester_id=workout.user_id))

    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_does_not_cascade_to_any_workout_session() -> None:
    """Confirms the documented non-cascading design: cancelling a Workout
    leaves any WorkoutSession untouched — this handler never even looks
    at a WorkoutSessionRepository."""
    workout = a_planned_workout()
    uow = FakeUnitOfWork(workouts=FakeWorkoutRepository({workout.id: workout}))
    handler = CancelWorkoutHandler(uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock())

    handler.handle(CancelWorkoutCommand(workout_id=workout.id, requester_id=workout.user_id))

    assert uow.sessions.added == []
