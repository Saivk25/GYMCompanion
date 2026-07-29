"""Domain events raised by the WorkoutSession aggregate.

Scoped to exactly the four events this increment's task named —
`WorkoutSessionStarted`, `WorkoutSessionCompleted`,
`WorkoutSessionAbandoned`, `WorkoutSessionNotesUpdated` — the same "raise
only what the aggregate's own methods actually do" discipline
`app.domain.user.events`, `app.domain.workout.events`, and
`app.domain.exercise.events` already follow.

Notably absent: a creation event. Every other aggregate in this codebase
(`UserRegistered`, `WorkoutPlanned`, `ExerciseCreated`) raises one from its
factory method; `WorkoutSession.plan()` does not, because this increment's
task specification names its four events starting from `...Started` —
see `docs/adr/0008-workout-session-execution-record.md` for the reasoning
this is a deliberate scope choice, not an oversight.
"""

from dataclasses import dataclass

from app.domain.shared_kernel.events import DomainEvent
from app.domain.user.identifiers import UserId
from app.domain.workout.identifiers import WorkoutId
from app.domain.workout_session.identifiers import WorkoutSessionId
from app.domain.workout_session.value_objects import (
    CompletionPercentage,
    SessionDuration,
    SessionNotes,
)


@dataclass(frozen=True, kw_only=True)
class WorkoutSessionStarted(DomainEvent):
    """`WorkoutSession.start(...)` moved the session to Active."""

    session_id: WorkoutSessionId
    workout_id: WorkoutId
    user_id: UserId


@dataclass(frozen=True, kw_only=True)
class WorkoutSessionCompleted(DomainEvent):
    """`WorkoutSession.complete(...)` moved the session to Completed.
    Carries `duration` and `completion_percentage` — the fields most
    documented downstream readers (PR detection, progressive overload,
    reports) would need first.
    """

    session_id: WorkoutSessionId
    workout_id: WorkoutId
    user_id: UserId
    duration: SessionDuration
    completion_percentage: CompletionPercentage


@dataclass(frozen=True, kw_only=True)
class WorkoutSessionAbandoned(DomainEvent):
    """`WorkoutSession.abandon(...)` moved the session to Abandoned, from
    either Planned or Active."""

    session_id: WorkoutSessionId
    workout_id: WorkoutId
    user_id: UserId


@dataclass(frozen=True, kw_only=True)
class WorkoutSessionNotesUpdated(DomainEvent):
    """`WorkoutSession.update_notes(...)` replaced the session's notes.
    Carries the full new `notes`, the same choice
    `app.domain.user.events.UserProfileUpdated` makes for its own
    full-value-object payload.
    """

    session_id: WorkoutSessionId
    notes: SessionNotes
