"""`WorkoutSessionContext`: a read-only snapshot of a WorkoutSession for
domain services.

Same purpose as `UserContext`, `WorkoutContext`, and `ExerciseContext`:
lets a future domain service — PR detection, progressive overload,
recovery, reporting (none built yet, all named in this increment's own
Goal) — consume everything it needs to know about one session in a single
immutable value.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.domain.shared_kernel.value_object import ValueObject
from app.domain.user.identifiers import UserId
from app.domain.workout.identifiers import WorkoutId
from app.domain.workout_session.enums import SessionStatus
from app.domain.workout_session.identifiers import WorkoutSessionId
from app.domain.workout_session.value_objects import (
    CompletionPercentage,
    SessionDate,
    SessionDuration,
    SessionNotes,
    SessionRating,
)

if TYPE_CHECKING:
    # Import only for the type checker — see UserContext's identical note
    # for why this avoids a real circular import at module load time.
    from app.domain.workout_session.workout_session import WorkoutSession


@dataclass(frozen=True, kw_only=True)
class WorkoutSessionContext(ValueObject):
    """An immutable snapshot of one WorkoutSession, taken at a point in
    time."""

    session_id: WorkoutSessionId
    workout_id: WorkoutId
    user_id: UserId
    status: SessionStatus
    session_date: SessionDate
    notes: SessionNotes
    duration: SessionDuration | None
    completion_percentage: CompletionPercentage | None
    rating: SessionRating | None

    @classmethod
    def from_workout_session(cls, session: WorkoutSession) -> WorkoutSessionContext:
        """Builds a snapshot from a live `WorkoutSession` aggregate. One-
        directional on purpose: `WorkoutSession` does not know this type
        exists.
        """
        return cls(
            session_id=session.id,
            workout_id=session.workout_id,
            user_id=session.user_id,
            status=session.status,
            session_date=session.session_date,
            notes=session.notes,
            duration=session.duration,
            completion_percentage=session.completion_percentage,
            rating=session.rating,
        )
