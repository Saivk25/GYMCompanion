"""Tests for app/application/workout/handlers/log_exercise_set_handler.py."""

import pytest

from app.application.workout.commands.log_exercise_set import LogExerciseSetCommand
from app.application.workout.handlers.log_exercise_set_handler import LogExerciseSetHandler
from app.domain.exercise.identifiers import ExerciseId
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.user.identifiers import UserId
from app.domain.workout_session.exercise_set import SetNumber, SetReps, SetRPE, SetWeight
from app.domain.workout_session.identifiers import WorkoutSessionId
from tests.application.workout.factories import (
    FakeExerciseRepository,
    FakeUnitOfWork,
    FakeWorkoutSessionRepository,
    OrderTrackingDispatcher,
    OrderTrackingUnitOfWork,
    RecordingDispatcher,
    a_created_exercise,
    a_fixed_clock,
    a_planned_session,
)


def _a_command(
    *, session_id: WorkoutSessionId, exercise_id: ExerciseId, requester_id: UserId
) -> LogExerciseSetCommand:
    return LogExerciseSetCommand(
        session_id=session_id,
        requester_id=requester_id,
        exercise_id=exercise_id,
        set_number=SetNumber(1),
        weight=SetWeight(100.0),
        reps=SetReps(5),
        rpe=SetRPE(7),
    )


@pytest.mark.unit
def test_logs_a_set_creating_a_new_performance_and_returns_its_id() -> None:
    session = a_planned_session()
    exercise = a_created_exercise()
    uow = FakeUnitOfWork(
        sessions=FakeWorkoutSessionRepository({session.id: session}),
        exercises=FakeExerciseRepository({exercise.id: exercise}),
    )
    handler = LogExerciseSetHandler(
        uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock()
    )

    result = handler.handle(
        _a_command(session_id=session.id, exercise_id=exercise.id, requester_id=session.user_id)
    )

    assert result.success is True
    assert result.value is not None
    assert len(session.exercise_performances) == 1
    performance = session.exercise_performances[0]
    assert performance.id == result.value
    assert len(performance.sets) == 1
    assert performance.sets[0].weight == SetWeight(100.0)


@pytest.mark.unit
def test_logging_a_second_set_reuses_the_existing_performance() -> None:
    session = a_planned_session()
    exercise = a_created_exercise()
    uow = FakeUnitOfWork(
        sessions=FakeWorkoutSessionRepository({session.id: session}),
        exercises=FakeExerciseRepository({exercise.id: exercise}),
    )
    handler = LogExerciseSetHandler(
        uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock()
    )

    first = handler.handle(
        _a_command(session_id=session.id, exercise_id=exercise.id, requester_id=session.user_id)
    )
    second_command = LogExerciseSetCommand(
        session_id=session.id,
        requester_id=session.user_id,
        exercise_id=exercise.id,
        set_number=SetNumber(2),
        weight=SetWeight(105.0),
        reps=SetReps(4),
        rpe=SetRPE(8),
    )
    second = handler.handle(second_command)

    assert first.value == second.value
    assert len(session.exercise_performances) == 1
    assert len(session.exercise_performances[0].sets) == 2


@pytest.mark.unit
def test_surfaces_exercise_recommendation_warnings() -> None:
    session = a_planned_session()
    exercise = a_created_exercise()
    uow = FakeUnitOfWork(
        sessions=FakeWorkoutSessionRepository({session.id: session}),
        exercises=FakeExerciseRepository({exercise.id: exercise}),
    )
    handler = LogExerciseSetHandler(
        uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock()
    )

    result = handler.handle(
        _a_command(session_id=session.id, exercise_id=exercise.id, requester_id=session.user_id)
    )

    assert result.success is True
    assert isinstance(result.warnings, tuple)


@pytest.mark.unit
def test_commits_and_dispatches_after_commit() -> None:
    session = a_planned_session()
    exercise = a_created_exercise()
    uow = FakeUnitOfWork(
        sessions=FakeWorkoutSessionRepository({session.id: session}),
        exercises=FakeExerciseRepository({exercise.id: exercise}),
    )
    dispatcher = RecordingDispatcher()
    handler = LogExerciseSetHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    handler.handle(
        _a_command(session_id=session.id, exercise_id=exercise.id, requester_id=session.user_id)
    )

    assert uow.committed is True
    # Two events: `ExerciseAddedToSession` (new performance created) and
    # `ExercisePerformanceUpdated` (the set itself logged).
    assert len(dispatcher.dispatched) == 2


@pytest.mark.unit
def test_dispatch_happens_strictly_after_commit() -> None:
    session = a_planned_session()
    exercise = a_created_exercise()
    call_order: list[str] = []
    uow = OrderTrackingUnitOfWork(
        sessions=FakeWorkoutSessionRepository({session.id: session}),
        exercises=FakeExerciseRepository({exercise.id: exercise}),
        call_order=call_order,
    )
    dispatcher = OrderTrackingDispatcher(call_order)
    handler = LogExerciseSetHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    handler.handle(
        _a_command(session_id=session.id, exercise_id=exercise.id, requester_id=session.user_id)
    )

    assert call_order == ["commit", "dispatch"]


@pytest.mark.unit
def test_a_missing_session_is_reported_as_a_failed_result_and_rolls_back() -> None:
    exercise = a_created_exercise()
    uow = FakeUnitOfWork(exercises=FakeExerciseRepository({exercise.id: exercise}))
    dispatcher = RecordingDispatcher()
    handler = LogExerciseSetHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(
        _a_command(
            session_id=WorkoutSessionId.generate(),
            exercise_id=exercise.id,
            requester_id=UserId.generate(),
        )
    )

    assert result.success is False
    assert "not found" in result.errors[0]
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_non_owner_requester_is_denied_and_rolls_back() -> None:
    session = a_planned_session()
    exercise = a_created_exercise()
    uow = FakeUnitOfWork(
        sessions=FakeWorkoutSessionRepository({session.id: session}),
        exercises=FakeExerciseRepository({exercise.id: exercise}),
    )
    dispatcher = RecordingDispatcher()
    handler = LogExerciseSetHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(
        _a_command(session_id=session.id, exercise_id=exercise.id, requester_id=UserId.generate())
    )

    assert result.success is False
    assert result.forbidden is True
    assert result.value is None
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_missing_exercise_is_reported_as_a_failed_result_and_rolls_back() -> None:
    session = a_planned_session()
    uow = FakeUnitOfWork(sessions=FakeWorkoutSessionRepository({session.id: session}))
    dispatcher = RecordingDispatcher()
    handler = LogExerciseSetHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(
        _a_command(
            session_id=session.id,
            exercise_id=ExerciseId.generate(),
            requester_id=session.user_id,
        )
    )

    assert result.success is False
    assert "not found" in result.errors[0]
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_commit_failure_is_reported_as_a_failed_result_and_rolls_back() -> None:
    session = a_planned_session()
    exercise = a_created_exercise()
    uow = FakeUnitOfWork(
        sessions=FakeWorkoutSessionRepository({session.id: session}),
        exercises=FakeExerciseRepository({exercise.id: exercise}),
        fail_on_commit=True,
    )
    dispatcher = RecordingDispatcher()
    handler = LogExerciseSetHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(
        _a_command(session_id=session.id, exercise_id=exercise.id, requester_id=session.user_id)
    )

    assert result.success is False
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_duplicate_set_number_raises_and_is_not_swallowed() -> None:
    session = a_planned_session()
    exercise = a_created_exercise()
    uow = FakeUnitOfWork(
        sessions=FakeWorkoutSessionRepository({session.id: session}),
        exercises=FakeExerciseRepository({exercise.id: exercise}),
    )
    dispatcher = RecordingDispatcher()
    handler = LogExerciseSetHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())
    handler.handle(
        _a_command(session_id=session.id, exercise_id=exercise.id, requester_id=session.user_id)
    )

    with pytest.raises(DomainInvariantViolationError, match="duplicate set number"):
        handler.handle(
            _a_command(session_id=session.id, exercise_id=exercise.id, requester_id=session.user_id)
        )
