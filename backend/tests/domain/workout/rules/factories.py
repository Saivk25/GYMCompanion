"""Shared test helpers for the Progressive Overload Rule Engine's test
suite.

Not itself a test file (no `test_` prefix, so pytest never collects it) —
mirrors `tests/domain/goal/rules/factories.py`'s reasoning exactly.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date

from app.domain.exercise.identifiers import ExerciseId
from app.domain.user.identifiers import UserId
from app.domain.workout.identifiers import WorkoutId
from app.domain.workout.rules.context import ProgressiveOverloadRuleContext, WorkoutSessionSummary
from app.domain.workout_session.context import ExercisePerformanceContext, WorkoutSessionContext
from app.domain.workout_session.enums import SessionStatus
from app.domain.workout_session.exercise_performance import PerformanceNotes
from app.domain.workout_session.exercise_set import (
    ExerciseSet,
    SetNumber,
    SetReps,
    SetRPE,
    SetWeight,
)
from app.domain.workout_session.identifiers import ExercisePerformanceId, WorkoutSessionId
from app.domain.workout_session.value_objects import SessionDate, SessionNotes


def an_exercise_set(
    *, set_number: int = 1, weight: float = 100.0, reps: int = 5, rpe: int = 7
) -> ExerciseSet:
    """A fully-populated `ExerciseSet` with sensible defaults, overridable
    per test. `completed` is deliberately not a parameter here —
    `WorkoutSessionSummary` counts every logged set regardless of that
    flag (see its own docstring), so no test in this package needs to
    vary it."""
    return ExerciseSet(
        set_number=SetNumber(set_number),
        weight=SetWeight(weight),
        reps=SetReps(reps),
        rpe=SetRPE(rpe),
    )


def a_session_context(
    *,
    session_date: date = date(2026, 1, 1),
    status: SessionStatus = SessionStatus.COMPLETED,
    sets: Sequence[ExerciseSet] = (),
) -> WorkoutSessionContext:
    """A `WorkoutSessionContext` with a single `ExercisePerformanceContext`
    holding the given sets (or no performances at all when `sets` is
    empty) — enough to exercise `WorkoutSessionSummary.from_session_context()`
    without needing a live `WorkoutSession` aggregate."""
    performances = (
        (
            ExercisePerformanceContext(
                performance_id=ExercisePerformanceId.generate(),
                exercise_id=ExerciseId.generate(),
                notes=PerformanceNotes(),
                sets=tuple(sets),
            ),
        )
        if sets
        else ()
    )
    return WorkoutSessionContext(
        session_id=WorkoutSessionId.generate(),
        workout_id=WorkoutId.generate(),
        user_id=UserId.generate(),
        status=status,
        session_date=SessionDate(session_date),
        notes=SessionNotes(),
        duration=None,
        completion_percentage=None,
        rating=None,
        exercise_performances=performances,
    )


def a_summary(
    *,
    session_date: date = date(2026, 1, 1),
    total_volume: float = 1000.0,
    average_load: float | None = 50.0,
    logged_set_count: int = 10,
) -> WorkoutSessionSummary:
    """A `WorkoutSessionSummary` built directly (not via
    `from_session_context()`) — every field this package's rules read is
    directly overridable, which is what most rule-level tests in this
    package need; `test_context.py` covers the `WorkoutSessionContext`-
    backed computation path separately."""
    return WorkoutSessionSummary(
        session_date=SessionDate(session_date),
        total_volume=total_volume,
        average_load=average_load,
        logged_set_count=logged_set_count,
    )


def a_context(*, sessions: Sequence[WorkoutSessionSummary] = ()) -> ProgressiveOverloadRuleContext:
    """A `ProgressiveOverloadRuleContext` wrapping the given summaries
    as-is (no sorting/filtering — direct construction, see that class's
    own docstring)."""
    return ProgressiveOverloadRuleContext(sessions=tuple(sessions))
