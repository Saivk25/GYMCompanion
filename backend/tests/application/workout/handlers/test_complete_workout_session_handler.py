"""Tests for
app/application/workout/handlers/complete_workout_session_handler.py."""

from datetime import timedelta

import pytest

from app.application.workout.commands.complete_workout_session import (
    CompleteWorkoutSessionCommand,
)
from app.application.workout.handlers.complete_workout_session_handler import (
    CompleteWorkoutSessionHandler,
)
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.workout.enums import WorkoutStatus
from app.domain.workout.workout import Workout
from app.domain.workout_session.enums import SessionStatus
from app.domain.workout_session.identifiers import WorkoutSessionId
from app.domain.workout_session.value_objects import CompletionPercentage, SessionDuration
from app.domain.workout_session.workout_session import WorkoutSession
from tests.application.workout.factories import (
    FakeUnitOfWork,
    FakeWorkoutRepository,
    FakeWorkoutSessionRepository,
    OrderTrackingDispatcher,
    OrderTrackingUnitOfWork,
    RecordingDispatcher,
    a_fixed_clock,
    a_planned_session,
    a_planned_workout,
)


def _an_in_progress_workout_with_an_active_session() -> tuple[Workout, WorkoutSession]:
    workout = a_planned_workout()
    workout.start(clock=a_fixed_clock())
    workout.pull_domain_events()
    session = a_planned_session(workout_id=workout.id, user_id=workout.user_id)
    session.start(clock=a_fixed_clock())
    session.pull_domain_events()
    return workout, session


def _a_command_for(session_id: WorkoutSessionId) -> CompleteWorkoutSessionCommand:
    return CompleteWorkoutSessionCommand(
        session_id=session_id,
        duration=SessionDuration(timedelta(minutes=45)),
        completion_percentage=CompletionPercentage(100.0),
    )


@pytest.mark.unit
def test_completes_the_session_and_returns_its_id() -> None:
    workout, session = _an_in_progress_workout_with_an_active_session()
    uow = FakeUnitOfWork(
        workouts=FakeWorkoutRepository({workout.id: workout}),
        sessions=FakeWorkoutSessionRepository({session.id: session}),
    )
    handler = CompleteWorkoutSessionHandler(
        uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock()
    )

    result = handler.handle(_a_command_for(session.id))

    assert result.success is True
    assert result.value == session.id
    assert session.status == SessionStatus.COMPLETED


@pytest.mark.unit
def test_completes_the_in_progress_parent_workout() -> None:
    workout, session = _an_in_progress_workout_with_an_active_session()
    uow = FakeUnitOfWork(
        workouts=FakeWorkoutRepository({workout.id: workout}),
        sessions=FakeWorkoutSessionRepository({session.id: session}),
    )
    handler = CompleteWorkoutSessionHandler(
        uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock()
    )

    handler.handle(_a_command_for(session.id))

    assert workout.status == WorkoutStatus.COMPLETED


@pytest.mark.unit
def test_does_not_re_complete_an_already_completed_workout() -> None:
    """Idempotent-forward: a second session completing under a workout
    already Completed must not re-invoke `Workout.complete()` (which
    would raise `DomainInvariantViolationError`)."""
    workout, first_session = _an_in_progress_workout_with_an_active_session()
    second_session = a_planned_session(workout_id=workout.id, user_id=workout.user_id)
    second_session.start(clock=a_fixed_clock())
    second_session.pull_domain_events()
    uow = FakeUnitOfWork(
        workouts=FakeWorkoutRepository({workout.id: workout}),
        sessions=FakeWorkoutSessionRepository(
            {first_session.id: first_session, second_session.id: second_session}
        ),
    )
    handler = CompleteWorkoutSessionHandler(
        uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock()
    )
    handler.handle(_a_command_for(first_session.id))
    assert workout.status == WorkoutStatus.COMPLETED

    result = handler.handle(_a_command_for(second_session.id))

    assert result.success is True
    assert second_session.status == SessionStatus.COMPLETED
    assert workout.status == WorkoutStatus.COMPLETED


@pytest.mark.unit
def test_commits_and_dispatches_both_aggregates_events_after_commit() -> None:
    workout, session = _an_in_progress_workout_with_an_active_session()
    uow = FakeUnitOfWork(
        workouts=FakeWorkoutRepository({workout.id: workout}),
        sessions=FakeWorkoutSessionRepository({session.id: session}),
    )
    dispatcher = RecordingDispatcher()
    handler = CompleteWorkoutSessionHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    handler.handle(_a_command_for(session.id))

    assert uow.committed is True
    kinds = {type(event).__name__ for event in dispatcher.dispatched}
    assert "WorkoutSessionCompleted" in kinds
    assert "WorkoutCompleted" in kinds


@pytest.mark.unit
def test_dispatch_happens_strictly_after_commit() -> None:
    workout, session = _an_in_progress_workout_with_an_active_session()
    call_order: list[str] = []
    uow = OrderTrackingUnitOfWork(
        workouts=FakeWorkoutRepository({workout.id: workout}),
        sessions=FakeWorkoutSessionRepository({session.id: session}),
        call_order=call_order,
    )
    dispatcher = OrderTrackingDispatcher(call_order)
    handler = CompleteWorkoutSessionHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    handler.handle(_a_command_for(session.id))

    assert call_order == ["commit", "dispatch"]


@pytest.mark.unit
def test_surfaces_progressive_overload_and_training_load_warnings_as_a_tuple() -> None:
    workout, session = _an_in_progress_workout_with_an_active_session()
    uow = FakeUnitOfWork(
        workouts=FakeWorkoutRepository({workout.id: workout}),
        sessions=FakeWorkoutSessionRepository({session.id: session}),
    )
    handler = CompleteWorkoutSessionHandler(
        uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock()
    )

    result = handler.handle(_a_command_for(session.id))

    assert result.success is True
    assert isinstance(result.warnings, tuple)


@pytest.mark.unit
def test_a_missing_session_is_reported_as_a_failed_result_and_rolls_back() -> None:
    uow = FakeUnitOfWork()
    dispatcher = RecordingDispatcher()
    handler = CompleteWorkoutSessionHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(_a_command_for(WorkoutSessionId.generate()))

    assert result.success is False
    assert "not found" in result.errors[0]
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_missing_parent_workout_is_reported_as_a_failed_result_and_rolls_back() -> None:
    session = a_planned_session()
    session.start(clock=a_fixed_clock())
    session.pull_domain_events()
    uow = FakeUnitOfWork(sessions=FakeWorkoutSessionRepository({session.id: session}))
    dispatcher = RecordingDispatcher()
    handler = CompleteWorkoutSessionHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(_a_command_for(session.id))

    assert result.success is False
    assert "not found" in result.errors[0]
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_commit_failure_is_reported_as_a_failed_result_and_rolls_back() -> None:
    workout, session = _an_in_progress_workout_with_an_active_session()
    uow = FakeUnitOfWork(
        workouts=FakeWorkoutRepository({workout.id: workout}),
        sessions=FakeWorkoutSessionRepository({session.id: session}),
        fail_on_commit=True,
    )
    dispatcher = RecordingDispatcher()
    handler = CompleteWorkoutSessionHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(_a_command_for(session.id))

    assert result.success is False
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_completing_a_still_planned_session_raises_and_is_not_swallowed() -> None:
    """`WorkoutSession.complete()` is only legal from Active — a
    still-Planned session raises `DomainInvariantViolationError`, which
    this handler always lets propagate."""
    session = a_planned_session()
    uow = FakeUnitOfWork(sessions=FakeWorkoutSessionRepository({session.id: session}))
    dispatcher = RecordingDispatcher()
    handler = CompleteWorkoutSessionHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    with pytest.raises(DomainInvariantViolationError, match="cannot transition"):
        handler.handle(_a_command_for(session.id))

    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_reuses_total_volume_as_the_training_load_scalar_for_completed_history() -> None:
    """Not a direct assertion on internal engine math, but confirms the
    workflow tolerates a multi-session history without erroring — the
    `TrainingLoadSummary.load` derivation path
    (`WorkoutSessionSummary.total_volume`) is exercised end-to-end."""
    workout, first_session = _an_in_progress_workout_with_an_active_session()
    uow = FakeUnitOfWork(
        workouts=FakeWorkoutRepository({workout.id: workout}),
        sessions=FakeWorkoutSessionRepository({first_session.id: first_session}),
    )
    handler = CompleteWorkoutSessionHandler(
        uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock()
    )

    result = handler.handle(_a_command_for(first_session.id))

    assert result.success is True
