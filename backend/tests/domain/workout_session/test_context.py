"""Tests for app/domain/workout_session/context.py."""

from dataclasses import FrozenInstanceError
from datetime import timedelta

import pytest

from app.domain.workout_session.context import ExercisePerformanceContext, WorkoutSessionContext
from app.domain.workout_session.enums import SessionStatus
from app.domain.workout_session.value_objects import CompletionPercentage, SessionDuration
from tests.domain.workout_session.factories import (
    a_fixed_clock,
    a_planned_session,
    an_exercise_id,
    an_exercise_set,
)


@pytest.mark.unit
def test_from_workout_session_snapshots_every_relevant_field() -> None:
    session = a_planned_session()

    context = WorkoutSessionContext.from_workout_session(session)

    assert context.session_id == session.id
    assert context.workout_id == session.workout_id
    assert context.user_id == session.user_id
    assert context.status == SessionStatus.PLANNED
    assert context.session_date == session.session_date
    assert context.notes == session.notes
    assert context.duration is None
    assert context.completion_percentage is None
    assert context.rating is None
    assert context.exercise_performances == ()


@pytest.mark.unit
def test_from_workout_session_snapshots_exercise_performances_and_their_sets() -> None:
    session = a_planned_session()
    clock = a_fixed_clock()
    exercise_id = an_exercise_id()
    performance_id = session.add_exercise(exercise_id, clock=clock)
    exercise_set = an_exercise_set(set_number=1)
    session.log_set(performance_id, exercise_set, clock=clock)

    context = WorkoutSessionContext.from_workout_session(session)

    assert len(context.exercise_performances) == 1
    performance_context = context.exercise_performances[0]
    assert isinstance(performance_context, ExercisePerformanceContext)
    assert performance_context.performance_id == performance_id
    assert performance_context.exercise_id == exercise_id
    assert performance_context.sets == (exercise_set,)


@pytest.mark.unit
def test_is_immutable() -> None:
    session = a_planned_session()
    context = WorkoutSessionContext.from_workout_session(session)
    with pytest.raises(FrozenInstanceError):
        context.status = SessionStatus.ABANDONED  # type: ignore[misc]


@pytest.mark.unit
def test_does_not_reflect_later_mutations_of_the_source_session() -> None:
    """A snapshot is a snapshot — mirrors the equivalent User/Workout/
    Exercise context tests."""
    session = a_planned_session()
    context = WorkoutSessionContext.from_workout_session(session)

    clock = a_fixed_clock()
    session.start(clock=clock)
    session.complete(
        duration=SessionDuration(timedelta(minutes=45)),
        completion_percentage=CompletionPercentage(100.0),
        clock=clock,
    )

    assert context.status == SessionStatus.PLANNED
    assert session.status == SessionStatus.COMPLETED
