"""The WorkoutSession aggregate: Sprint 2's fourth real aggregate, built on
the Sprint 1 shared kernel (`app.domain.shared_kernel`) and following the
same pattern as `app.domain.user`, `app.domain.workout`, and
`app.domain.exercise`. Training bounded context (Domain Model & Decision
Engine Bible, Section 3, Table 2), closest deep dive in Section 4.7
(`WorkoutSession`).

The execution record of a `Workout`: `Workout` is the plan, `WorkoutSession`
is what actually happened. See
`docs/adr/0008-workout-session-execution-record.md` for the full reasoning,
including why this increment's four events start at `...Started` (no
creation event, unlike every other aggregate here) and why
`update_notes()` is not blocked once the session is Completed or Abandoned
(unlike `Workout`/`Exercise`'s equivalent methods).

Scope of this increment — deliberately smaller than the Bible's full
`WorkoutSession`, not an oversight: `ExerciseSet`/`LoggedExercise` (the
individual logged sets a session actually contains), progressive overload,
and rest timers are not modeled yet.

Depends on nothing outside the Python standard library,
`app.domain.shared_kernel`, `app.domain.user` (for the owning `UserId`),
and `app.domain.workout` (for the executed `WorkoutId`) — enforced by the
same statically-checked rule as the rest of `app/domain`
(`tests/domain/test_import_boundaries.py`).
"""

from app.domain.workout_session.context import WorkoutSessionContext
from app.domain.workout_session.enums import SessionStatus
from app.domain.workout_session.events import (
    WorkoutSessionAbandoned,
    WorkoutSessionCompleted,
    WorkoutSessionNotesUpdated,
    WorkoutSessionStarted,
)
from app.domain.workout_session.identifiers import WorkoutSessionId
from app.domain.workout_session.repository import WorkoutSessionRepository
from app.domain.workout_session.value_objects import (
    CompletionPercentage,
    SessionDate,
    SessionDuration,
    SessionNotes,
    SessionRating,
)
from app.domain.workout_session.workout_session import WorkoutSession

__all__ = [
    "CompletionPercentage",
    "SessionDate",
    "SessionDuration",
    "SessionNotes",
    "SessionRating",
    "SessionStatus",
    "WorkoutSession",
    "WorkoutSessionAbandoned",
    "WorkoutSessionCompleted",
    "WorkoutSessionContext",
    "WorkoutSessionId",
    "WorkoutSessionNotesUpdated",
    "WorkoutSessionRepository",
    "WorkoutSessionStarted",
]
