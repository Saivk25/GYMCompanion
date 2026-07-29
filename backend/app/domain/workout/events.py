"""Domain events raised by the Workout aggregate.

Scoped to exactly the four lifecycle transitions this increment's task
named — `WorkoutPlanned`, `WorkoutStarted`, `WorkoutCompleted`,
`WorkoutCancelled` — mirroring `app.domain.user.events`'s discipline of
raising only what the aggregate's own methods actually do, not every event
the Bible eventually names for the closest analogous concept
(`WorkoutSession`'s `SessionScheduled`/`SessionStarted`/`SessionCompleted`
plus `SetLogged`, `PRAchieved`, `HabitStreakExtended`, none of which this
increment's `Workout` has the supporting aggregates for yet — see
`docs/adr/0006-workout-aggregate-first-increment.md`). Add a new event only
once a real subscriber needs it.
"""

from dataclasses import dataclass

from app.domain.shared_kernel.events import DomainEvent
from app.domain.user.identifiers import UserId
from app.domain.workout.identifiers import WorkoutId
from app.domain.workout.value_objects import WorkoutDate, WorkoutDuration, WorkoutName


@dataclass(frozen=True, kw_only=True)
class WorkoutPlanned(DomainEvent):
    """A new Workout was created via `Workout.plan(...)`. Carries `name`
    and `planned_date` since a first subscriber (a dashboard, a reminder)
    would need them immediately without re-fetching the aggregate.
    """

    workout_id: WorkoutId
    user_id: UserId
    name: WorkoutName
    planned_date: WorkoutDate


@dataclass(frozen=True, kw_only=True)
class WorkoutStarted(DomainEvent):
    """`Workout.start(...)` moved the workout to InProgress."""

    workout_id: WorkoutId
    user_id: UserId


@dataclass(frozen=True, kw_only=True)
class WorkoutCompleted(DomainEvent):
    """`Workout.complete(...)` moved the workout to Completed. Carries the
    logged `duration` — the field most documented downstream readers
    (streaks, weekly adherence) would need first.
    """

    workout_id: WorkoutId
    user_id: UserId
    duration: WorkoutDuration


@dataclass(frozen=True, kw_only=True)
class WorkoutCancelled(DomainEvent):
    """`Workout.cancel(...)` moved the workout to Cancelled, from either
    Planned or InProgress."""

    workout_id: WorkoutId
    user_id: UserId
