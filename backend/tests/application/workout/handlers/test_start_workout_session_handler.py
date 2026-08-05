"""Tests for
app/application/workout/handlers/start_workout_session_handler.py."""

from datetime import date, timedelta

import pytest

from app.application.workout.commands.start_workout_session import StartWorkoutSessionCommand
from app.application.workout.handlers.start_workout_session_handler import (
    StartWorkoutSessionHandler,
)
from app.domain.user.identifiers import UserId
from app.domain.workout.enums import WorkoutStatus
from app.domain.workout.identifiers import WorkoutId
from app.domain.workout.value_objects import WorkoutDuration
from app.domain.workout_session.value_objects import SessionDate
from tests.application.workout.factories import (
    FakeUnitOfWork,
    FakeWorkoutRepository,
    FakeWorkoutSessionRepository,
    OrderTrackingDispatcher,
    OrderTrackingUnitOfWork,
    RecordingDispatcher,
    a_fixed_clock,
    a_planned_workout,
)

_A_COMMAND = StartWorkoutSessionCommand(
    workout_id=WorkoutId.generate(),
    requester_id=UserId.generate(),
    session_date=SessionDate(date(2026, 1, 1)),
)


def _command_for(workout_id: WorkoutId, *, requester_id: UserId) -> StartWorkoutSessionCommand:
    return StartWorkoutSessionCommand(
        workout_id=workout_id,
        requester_id=requester_id,
        session_date=SessionDate(date(2026, 1, 1)),
    )


@pytest.mark.unit
def test_starts_a_session_and_returns_its_id() -> None:
    workout = a_planned_workout()
    uow = FakeUnitOfWork(workouts=FakeWorkoutRepository({workout.id: workout}))
    handler = StartWorkoutSessionHandler(
        uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock()
    )

    result = handler.handle(_command_for(workout.id, requester_id=workout.user_id))

    assert result.success is True
    assert result.value is not None
    session = uow.sessions.get(result.value)
    assert session is not None
    assert session.workout_id == workout.id
    assert session.user_id == workout.user_id


@pytest.mark.unit
def test_advances_a_planned_workout_to_in_progress() -> None:
    workout = a_planned_workout()
    uow = FakeUnitOfWork(workouts=FakeWorkoutRepository({workout.id: workout}))
    handler = StartWorkoutSessionHandler(
        uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock()
    )

    handler.handle(_command_for(workout.id, requester_id=workout.user_id))

    assert workout.status == WorkoutStatus.IN_PROGRESS


@pytest.mark.unit
def test_does_not_re_start_a_workout_already_in_progress() -> None:
    """Idempotent-forward: starting a second session under a workout
    already InProgress must not re-invoke `Workout.start()` (which
    would raise `DomainInvariantViolationError`)."""
    workout = a_planned_workout()
    workout.start(clock=a_fixed_clock())
    workout.pull_domain_events()
    uow = FakeUnitOfWork(workouts=FakeWorkoutRepository({workout.id: workout}))
    handler = StartWorkoutSessionHandler(
        uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock()
    )

    result = handler.handle(_command_for(workout.id, requester_id=workout.user_id))

    assert result.success is True
    assert workout.status == WorkoutStatus.IN_PROGRESS


@pytest.mark.unit
def test_commits_and_dispatches_both_aggregates_events() -> None:
    workout = a_planned_workout()
    uow = FakeUnitOfWork(workouts=FakeWorkoutRepository({workout.id: workout}))
    dispatcher = RecordingDispatcher()
    handler = StartWorkoutSessionHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    handler.handle(_command_for(workout.id, requester_id=workout.user_id))

    assert uow.committed is True
    kinds = {type(event).__name__ for event in dispatcher.dispatched}
    assert "WorkoutStarted" in kinds
    assert "WorkoutSessionStarted" in kinds


@pytest.mark.unit
def test_dispatch_happens_strictly_after_commit() -> None:
    workout = a_planned_workout()
    call_order: list[str] = []
    uow = OrderTrackingUnitOfWork(
        workouts=FakeWorkoutRepository({workout.id: workout}), call_order=call_order
    )
    dispatcher = OrderTrackingDispatcher(call_order)
    handler = StartWorkoutSessionHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    handler.handle(_command_for(workout.id, requester_id=workout.user_id))

    assert call_order == ["commit", "dispatch"]


@pytest.mark.unit
def test_a_missing_workout_is_reported_as_a_failed_result_and_rolls_back() -> None:
    uow = FakeUnitOfWork()
    dispatcher = RecordingDispatcher()
    handler = StartWorkoutSessionHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(_A_COMMAND)

    assert result.success is False
    assert "not found" in result.errors[0]
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_non_owner_requester_is_denied_and_rolls_back() -> None:
    """`requester_id` is compared against the parent Workout's own
    `user_id` — the only aggregate loaded at this point, since no
    WorkoutSession exists yet to check ownership against."""
    workout = a_planned_workout()
    uow = FakeUnitOfWork(workouts=FakeWorkoutRepository({workout.id: workout}))
    dispatcher = RecordingDispatcher()
    handler = StartWorkoutSessionHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(_command_for(workout.id, requester_id=UserId.generate()))

    assert result.success is False
    assert result.forbidden is True
    assert result.value is None
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []
    assert uow.sessions.added == []


@pytest.mark.unit
def test_cannot_start_a_session_for_a_completed_workout() -> None:
    workout = a_planned_workout()
    workout.start(clock=a_fixed_clock())
    workout.complete(duration=WorkoutDuration(timedelta(minutes=30)), clock=a_fixed_clock())
    workout.pull_domain_events()
    uow = FakeUnitOfWork(workouts=FakeWorkoutRepository({workout.id: workout}))
    dispatcher = RecordingDispatcher()
    handler = StartWorkoutSessionHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(_command_for(workout.id, requester_id=workout.user_id))

    assert result.success is False
    assert "status" in result.errors[0]
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_cannot_start_a_session_for_a_cancelled_workout() -> None:
    workout = a_planned_workout()
    workout.cancel(clock=a_fixed_clock())
    workout.pull_domain_events()
    uow = FakeUnitOfWork(workouts=FakeWorkoutRepository({workout.id: workout}))
    dispatcher = RecordingDispatcher()
    handler = StartWorkoutSessionHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(_command_for(workout.id, requester_id=workout.user_id))

    assert result.success is False
    assert uow.rolled_back is True


@pytest.mark.unit
def test_a_session_repository_add_failure_is_reported_as_a_failed_result() -> None:
    workout = a_planned_workout()
    uow = FakeUnitOfWork(
        workouts=FakeWorkoutRepository({workout.id: workout}),
        sessions=FakeWorkoutSessionRepository(fail_on_add=True),
    )
    handler = StartWorkoutSessionHandler(
        uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock()
    )

    result = handler.handle(_command_for(workout.id, requester_id=workout.user_id))

    assert result.success is False
    assert "already exists" in result.errors[0]


@pytest.mark.unit
def test_a_commit_failure_is_reported_as_a_failed_result_and_rolls_back() -> None:
    workout = a_planned_workout()
    uow = FakeUnitOfWork(workouts=FakeWorkoutRepository({workout.id: workout}), fail_on_commit=True)
    dispatcher = RecordingDispatcher()
    handler = StartWorkoutSessionHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(_command_for(workout.id, requester_id=workout.user_id))

    assert result.success is False
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_generates_a_distinct_session_id_each_call() -> None:
    workout = a_planned_workout()
    uow = FakeUnitOfWork(workouts=FakeWorkoutRepository({workout.id: workout}))
    handler = StartWorkoutSessionHandler(
        uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock()
    )

    first = handler.handle(_command_for(workout.id, requester_id=workout.user_id))
    second = handler.handle(_command_for(workout.id, requester_id=workout.user_id))

    assert first.value != second.value
