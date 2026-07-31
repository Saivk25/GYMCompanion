"""`WorkoutSessionDTO`: the read-only projection of a `WorkoutSession`
aggregate returned to whatever calls a WorkoutSession query handler.

Not the same type as `app.domain.workout_session.context.
WorkoutSessionContext` — identical reasoning to `WorkoutDTO`'s own
module docstring, applied to this aggregate. `ExercisePerformanceDTO`
lives in this same file rather than a separate module: it exists only
as `WorkoutSessionDTO`'s own nested shape, the same one-file-per-
top-level-DTO discipline the task's own file list implies (`dto/
workout_dto.py`, `dto/workout_session_dto.py` — no separate file for a
DTO that is never returned on its own).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from app.domain.exercise.identifiers import ExerciseId
from app.domain.user.identifiers import UserId
from app.domain.workout.identifiers import WorkoutId
from app.domain.workout_session.enums import SessionStatus
from app.domain.workout_session.exercise_performance import PerformanceNotes
from app.domain.workout_session.exercise_set import ExerciseSet
from app.domain.workout_session.identifiers import ExercisePerformanceId, WorkoutSessionId
from app.domain.workout_session.value_objects import (
    CompletionPercentage,
    SessionDate,
    SessionDuration,
    SessionNotes,
    SessionRating,
)

if TYPE_CHECKING:
    # Import only for the type checker — see UserDTO's identical note
    # for why this avoids a real circular import at module load time.
    from app.domain.workout_session.exercise_performance import ExercisePerformance
    from app.domain.workout_session.workout_session import WorkoutSession


@dataclass(frozen=True, kw_only=True)
class ExercisePerformanceDTO:
    """An immutable, read-only snapshot of one `ExercisePerformance`,
    nested inside a `WorkoutSessionDTO`."""

    performance_id: ExercisePerformanceId
    exercise_id: ExerciseId
    notes: PerformanceNotes
    sets: tuple[ExerciseSet, ...]

    @classmethod
    def from_exercise_performance(cls, performance: ExercisePerformance) -> ExercisePerformanceDTO:
        return cls(
            performance_id=performance.id,
            exercise_id=performance.exercise_id,
            notes=performance.notes,
            sets=performance.sets,
        )


@dataclass(frozen=True, kw_only=True)
class WorkoutSessionDTO:
    """An immutable, read-only snapshot of one `WorkoutSession`, taken
    at query time."""

    session_id: WorkoutSessionId
    workout_id: WorkoutId
    user_id: UserId
    status: SessionStatus
    session_date: SessionDate
    planned_at: datetime
    notes: SessionNotes
    duration: SessionDuration | None
    completion_percentage: CompletionPercentage | None
    rating: SessionRating | None
    started_at: datetime | None
    completed_at: datetime | None
    abandoned_at: datetime | None
    exercise_performances: tuple[ExercisePerformanceDTO, ...]

    @classmethod
    def from_workout_session(cls, session: WorkoutSession) -> WorkoutSessionDTO:
        """Builds a DTO from a live `WorkoutSession` aggregate. One-
        directional on purpose, mirroring `UserDTO.from_user`.
        """
        return cls(
            session_id=session.id,
            workout_id=session.workout_id,
            user_id=session.user_id,
            status=session.status,
            session_date=session.session_date,
            planned_at=session.planned_at,
            notes=session.notes,
            duration=session.duration,
            completion_percentage=session.completion_percentage,
            rating=session.rating,
            started_at=session.started_at,
            completed_at=session.completed_at,
            abandoned_at=session.abandoned_at,
            exercise_performances=tuple(
                ExercisePerformanceDTO.from_exercise_performance(performance)
                for performance in session.exercise_performances
            ),
        )
