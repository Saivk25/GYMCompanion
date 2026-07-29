"""Immutable value objects owned by the Workout aggregate.

Every type here is a `ValueObject` subclass (`app.domain.shared_kernel`):
no identity, replaced wholesale on change, validated once at construction
so an instance is either fully valid or doesn't exist — the same discipline
`app.domain.user.value_objects` follows.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from app.domain.shared_kernel.validation import ensure, ensure_not_empty
from app.domain.shared_kernel.value_object import ValueObject

_MAX_WORKOUT_NAME_LENGTH = 200
_MAX_WORKOUT_GOAL_LENGTH = 200
_MAX_WORKOUT_NOTES_LENGTH = 2000


@dataclass(frozen=True)
class WorkoutName(ValueObject):
    """What the user (or a future Plan Generator) calls this workout, e.g.
    `WorkoutName("Push Day")`. Required on every `Workout` — "Workout name
    cannot be empty" is one of the invariants this aggregate must enforce,
    and this is where it's enforced: in the value object itself, the same
    placement `UserProfile` uses for its own field-level rules.
    """

    value: str

    def __post_init__(self) -> None:
        ensure_not_empty(self.value, "workout name")
        ensure(
            len(self.value) <= _MAX_WORKOUT_NAME_LENGTH,
            f"workout name must be at most {_MAX_WORKOUT_NAME_LENGTH} characters, "
            f"got {len(self.value)}",
        )


@dataclass(frozen=True)
class WorkoutGoal(ValueObject):
    """A short, free-text purpose for this specific workout, e.g.
    `WorkoutGoal("upper body strength")`.

    Deliberately not a reference to the Domain Model & Decision Engine
    Bible's `Goal` aggregate (Section 4.4) — that represents a longer-
    horizon objective ("lose 5kg by June") a user ranks and tracks across
    many workouts, doesn't exist in this codebase yet, and is a different
    concept from what a single workout is *for* today. `Workout.goal` may
    reference a real `Goal` once that aggregate exists and a documented
    need for the link shows up; inventing that reference speculatively now
    would be exactly the kind of premature coupling this project's
    engineering principles argue against.
    """

    value: str

    def __post_init__(self) -> None:
        ensure_not_empty(self.value, "workout goal")
        ensure(
            len(self.value) <= _MAX_WORKOUT_GOAL_LENGTH,
            f"workout goal must be at most {_MAX_WORKOUT_GOAL_LENGTH} characters, "
            f"got {len(self.value)}",
        )


@dataclass(frozen=True)
class WorkoutNotes(ValueObject):
    """Free-text notes on the workout — Product Bible: "Workout logger:
    sets, reps, load/band, time, RIR, pain, notes" (MVP tier).

    Validated non-empty on the same principle as `WorkoutGoal`: if there's
    nothing to say, `Workout.notes` should be `None`, not a `WorkoutNotes`
    holding an empty string — two ways to represent "no notes" would be a
    real, if minor, source of bugs (an equality check or a "has notes"
    check would need to handle both).
    """

    value: str

    def __post_init__(self) -> None:
        ensure_not_empty(self.value, "workout notes")
        ensure(
            len(self.value) <= _MAX_WORKOUT_NOTES_LENGTH,
            f"workout notes must be at most {_MAX_WORKOUT_NOTES_LENGTH} characters, "
            f"got {len(self.value)}",
        )


@dataclass(frozen=True)
class WorkoutDuration(ValueObject):
    """How long the workout took, as a `datetime.timedelta`.

    Supplied by the caller at `Workout.complete(...)` rather than derived
    purely from `started_at`/`completed_at` timestamps: a user logging how
    long they actually trained (Product Bible's "Workout logger: ... time
    ...") legitimately differs from raw wall-clock elapsed time — breaks,
    a paused session, warm-up not counted, or a manually logged workout
    with no live start/stop at all (Product Bible: "Manual workout/text-
    paste import", MVP). Because it's an external input, it needs its own
    validation rather than inheriting correctness from two clock reads —
    "Duration cannot be negative" is enforced right here.
    """

    value: timedelta

    def __post_init__(self) -> None:
        ensure(
            self.value >= timedelta(0),
            f"workout duration must not be negative, got {self.value}",
        )


@dataclass(frozen=True)
class WorkoutDate(ValueObject):
    """The calendar date this workout is planned for (or was performed on,
    for a manually logged past workout) — a `datetime.date`, not a
    `datetime`, since a workout belongs to a day, not an instant. Required
    on every `Workout` ("Workout date must exist"); the type system
    already enforces "must exist" for anyone constructing a `Workout` (the
    parameter isn't `Optional`), so this value object's own job is only to
    wrap the date, not to second-guess which dates are plausible — a
    retroactively logged workout from months ago and a workout planned
    months ahead are both legitimate.
    """

    value: date
