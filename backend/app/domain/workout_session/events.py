"""Domain events raised by the WorkoutSession aggregate.

Scoped to exactly the events named across this aggregate's two increments —
`WorkoutSessionStarted`, `WorkoutSessionCompleted`,
`WorkoutSessionAbandoned`, `WorkoutSessionNotesUpdated` (Sprint 2 Step 4),
plus `ExerciseAddedToSession`, `ExerciseRemovedFromSession`,
`ExerciseSetCompleted`, `ExercisePerformanceUpdated` (Sprint 2 Step 5) — the
same "raise only what the aggregate's own methods actually do" discipline
`app.domain.user.events`, `app.domain.workout.events`, and
`app.domain.exercise.events` already follow.

Notably absent: a creation event. Every other aggregate in this codebase
(`UserRegistered`, `WorkoutPlanned`, `ExerciseCreated`) raises one from its
factory method; `WorkoutSession.plan()` does not, because this increment's
task specification names its four events starting from `...Started` —
see `docs/adr/0008-workout-session-execution-record.md` for the reasoning
this is a deliberate scope choice, not an oversight.

The Step 5 events carry `performance_id` (`ExercisePerformanceId`) rather
than the `ExercisePerformance` entity itself — an event is a fact that
already happened, immutable forever, and must never hold a reference to a
live, still-mutable domain object; every event in this module already
follows that discipline for `WorkoutSession` itself (`session_id`, not
`self`), and the same reasoning applies one level down.
"""

from dataclasses import dataclass

from app.domain.exercise.identifiers import ExerciseId
from app.domain.shared_kernel.events import DomainEvent
from app.domain.user.identifiers import UserId
from app.domain.workout.identifiers import WorkoutId
from app.domain.workout_session.exercise_set import ExerciseSet
from app.domain.workout_session.identifiers import ExercisePerformanceId, WorkoutSessionId
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


@dataclass(frozen=True, kw_only=True)
class ExerciseAddedToSession(DomainEvent):
    """`WorkoutSession.add_exercise(...)` created a new
    `ExercisePerformance` for `exercise_id` within this session."""

    session_id: WorkoutSessionId
    performance_id: ExercisePerformanceId
    exercise_id: ExerciseId


@dataclass(frozen=True, kw_only=True)
class ExerciseRemovedFromSession(DomainEvent):
    """`WorkoutSession.remove_exercise(...)` removed a previously added
    `ExercisePerformance`. Carries `exercise_id` alongside `performance_id`
    so a listener doesn't need to have already cached which exercise the
    removed performance was for."""

    session_id: WorkoutSessionId
    performance_id: ExercisePerformanceId
    exercise_id: ExerciseId


@dataclass(frozen=True, kw_only=True)
class ExerciseSetCompleted(DomainEvent):
    """`WorkoutSession.complete_set(...)` marked one logged set complete.
    Carries the completed `ExerciseSet` itself (weight/reps/RPE/set
    number) — the same "carry what the most-documented downstream readers
    would need first" choice `WorkoutSessionCompleted` already makes,
    anticipating PR detection and progressive overload without
    implementing either here.
    """

    session_id: WorkoutSessionId
    performance_id: ExercisePerformanceId
    exercise_id: ExerciseId
    exercise_set: ExerciseSet


@dataclass(frozen=True, kw_only=True)
class ExercisePerformanceUpdated(DomainEvent):
    """A catch-all for changes to an `ExercisePerformance` that don't have
    their own dedicated event: a new set logged (`WorkoutSession.
    log_set(...)`) or the performance's notes replaced (`WorkoutSession.
    update_exercise_notes(...)`). Mirrors `WorkoutSessionNotesUpdated`'s
    role at the session level — this task names exactly four
    exercise-performance events, so "a set was logged" and "notes were
    updated" share this one rather than each getting a bespoke event.
    """

    session_id: WorkoutSessionId
    performance_id: ExercisePerformanceId
    exercise_id: ExerciseId
