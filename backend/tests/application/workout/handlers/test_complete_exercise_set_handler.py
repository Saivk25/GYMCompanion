"""Tests for
app/application/workout/handlers/complete_exercise_set_handler.py."""

import pytest

from app.application.workout.commands.complete_exercise_set import CompleteExerciseSetCommand
from app.application.workout.handlers.complete_exercise_set_handler import (
    CompleteExerciseSetHandler,
)
from app.domain.exercise.identifiers import ExerciseId
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.workout_session.exercise_set import (
    ExerciseSet,
    SetNumber,
    SetReps,
    SetRPE,
    SetWeight,
)
from app.domain.workout_session.identifiers import ExercisePerformanceId, WorkoutSessionId
from app.domain.workout_session.workout_session import WorkoutSession
from tests.application.workout.factories import (
    FakeUnitOfWork,
    FakeWorkoutSessionRepository,
    OrderTrackingDispatcher,
    OrderTrackingUnitOfWork,
    RecordingDispatcher,
    a_fixed_clock,
    a_planned_session,
)


def _a_session_with_a_logged_set() -> tuple[WorkoutSession, ExercisePerformanceId]:
    session = a_planned_session()
    performance_id = session.add_exercise(ExerciseId.generate(), clock=a_fixed_clock())
    session.log_set(
        performance_id,
        ExerciseSet(
            set_number=SetNumber(1), weight=SetWeight(100.0), reps=SetReps(5), rpe=SetRPE(7)
        ),
        clock=a_fixed_clock(),
    )
    session.pull_domain_events()
    return session, performance_id


@pytest.mark.unit
def test_marks_a_set_complete_and_returns_the_session_id() -> None:
    session, performance_id = _a_session_with_a_logged_set()
    uow = FakeUnitOfWork(sessions=FakeWorkoutSessionRepository({session.id: session}))
    handler = CompleteExerciseSetHandler(
        uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock()
    )

    result = handler.handle(
        CompleteExerciseSetCommand(
            session_id=session.id, performance_id=performance_id, set_number=1
        )
    )

    assert result.success is True
    assert result.value == session.id
    performance = next(p for p in session.exercise_performances if p.id == performance_id)
    assert performance.sets[0].completed is True


@pytest.mark.unit
def test_commits_and_dispatches_after_commit() -> None:
    session, performance_id = _a_session_with_a_logged_set()
    uow = FakeUnitOfWork(sessions=FakeWorkoutSessionRepository({session.id: session}))
    dispatcher = RecordingDispatcher()
    handler = CompleteExerciseSetHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    handler.handle(
        CompleteExerciseSetCommand(
            session_id=session.id, performance_id=performance_id, set_number=1
        )
    )

    assert uow.committed is True
    assert len(dispatcher.dispatched) == 1


@pytest.mark.unit
def test_dispatch_happens_strictly_after_commit() -> None:
    session, performance_id = _a_session_with_a_logged_set()
    call_order: list[str] = []
    uow = OrderTrackingUnitOfWork(
        sessions=FakeWorkoutSessionRepository({session.id: session}), call_order=call_order
    )
    dispatcher = OrderTrackingDispatcher(call_order)
    handler = CompleteExerciseSetHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    handler.handle(
        CompleteExerciseSetCommand(
            session_id=session.id, performance_id=performance_id, set_number=1
        )
    )

    assert call_order == ["commit", "dispatch"]


@pytest.mark.unit
def test_a_missing_session_is_reported_as_a_failed_result_and_rolls_back() -> None:
    uow = FakeUnitOfWork()
    dispatcher = RecordingDispatcher()
    handler = CompleteExerciseSetHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(
        CompleteExerciseSetCommand(
            session_id=WorkoutSessionId.generate(),
            performance_id=ExercisePerformanceId.generate(),
            set_number=1,
        )
    )

    assert result.success is False
    assert "not found" in result.errors[0]
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_commit_failure_is_reported_as_a_failed_result_and_rolls_back() -> None:
    session, performance_id = _a_session_with_a_logged_set()
    uow = FakeUnitOfWork(
        sessions=FakeWorkoutSessionRepository({session.id: session}), fail_on_commit=True
    )
    dispatcher = RecordingDispatcher()
    handler = CompleteExerciseSetHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(
        CompleteExerciseSetCommand(
            session_id=session.id, performance_id=performance_id, set_number=1
        )
    )

    assert result.success is False
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_completing_an_unknown_set_number_raises_and_is_not_swallowed() -> None:
    session, performance_id = _a_session_with_a_logged_set()
    uow = FakeUnitOfWork(sessions=FakeWorkoutSessionRepository({session.id: session}))
    dispatcher = RecordingDispatcher()
    handler = CompleteExerciseSetHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    with pytest.raises(DomainInvariantViolationError, match="no set numbered"):
        handler.handle(
            CompleteExerciseSetCommand(
                session_id=session.id, performance_id=performance_id, set_number=99
            )
        )

    assert dispatcher.dispatched == []
