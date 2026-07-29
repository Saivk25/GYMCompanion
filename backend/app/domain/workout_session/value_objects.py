"""Immutable value objects owned by the WorkoutSession aggregate.

Every type here is a `ValueObject` subclass (`app.domain.shared_kernel`):
no identity, replaced wholesale on change, validated once at construction —
the same discipline `app.domain.user.value_objects`,
`app.domain.workout.value_objects`, and `app.domain.exercise.value_objects`
follow.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from app.domain.shared_kernel.validation import ensure
from app.domain.shared_kernel.value_object import ValueObject

_MAX_SESSION_NOTES_LENGTH = 2000

# The Domain Model & Decision Engine Bible names `RPE` as a key attribute
# of the real `WorkoutSession` (Section 4.7, Table 10: "RPE/pain are
# range-checked at entry") without pinning down its exact numeric range.
# 1-10 is the industry-standard Rate of Perceived Exertion scale (the Borg
# CR10 scale most fitness apps and coaching literature already use) — this
# increment's own choice of bound, not a value the Bible specifies.
_MIN_SESSION_RATING = 1
_MAX_SESSION_RATING = 10

_MIN_COMPLETION_PERCENTAGE = 0.0
_MAX_COMPLETION_PERCENTAGE = 100.0


@dataclass(frozen=True)
class SessionDate(ValueObject):
    """The calendar date this session happened (or is planned for) — a
    `datetime.date`, not a `datetime`, the same reasoning
    `app.domain.workout.value_objects.WorkoutDate` documents: a session
    belongs to a day, not an instant.
    """

    value: date


@dataclass(frozen=True)
class SessionDuration(ValueObject):
    """How long the session actually took, as a `datetime.timedelta`.

    "Duration must be positive" here — strictly greater than zero — which
    is deliberately stricter than
    `app.domain.workout.value_objects.WorkoutDuration`'s "must not be
    negative" (which allows exactly zero). A `Workout` can plausibly be
    marked complete with a zero-length placeholder duration if the actual
    time genuinely wasn't tracked; a `WorkoutSession` is specifically the
    execution *record* — a session with a recorded duration of zero would
    be a data-entry mistake, not a legitimate "no time logged" state, so
    it's rejected rather than silently allowed like `WorkoutDuration` does.
    """

    value: timedelta

    def __post_init__(self) -> None:
        ensure(
            self.value > timedelta(0),
            f"session duration must be positive, got {self.value}",
        )


@dataclass(frozen=True)
class SessionNotes(ValueObject):
    """Free-text notes on the session.

    "Notes may be empty" is an explicit, deliberate divergence from
    `app.domain.workout.value_objects.WorkoutNotes` and
    `app.domain.exercise.value_objects.ExerciseDescription`, both of which
    require non-empty content and rely on the *absence* of a value object
    (`None`) to represent "nothing to say." Here, an empty string is
    itself a valid, always-present value — `WorkoutSession.notes` is never
    `None`, only ever a `SessionNotes` that may happen to be empty. Two
    different, equally valid ways value objects in this codebase represent
    "no notes yet"; which one applies is a rule this task states
    explicitly per aggregate, not a fixed convention.
    """

    value: str = ""

    def __post_init__(self) -> None:
        ensure(
            len(self.value) <= _MAX_SESSION_NOTES_LENGTH,
            f"session notes must be at most {_MAX_SESSION_NOTES_LENGTH} characters, "
            f"got {len(self.value)}",
        )


@dataclass(frozen=True)
class SessionRating(ValueObject):
    """A self-reported 1-10 rating of how the session went — see the
    module-level comment above for why 1-10. Read by future recovery and
    coaching logic (not yet implemented) alongside `SessionNotes` as a
    subjective counterpart to objective logged data.
    """

    value: int

    def __post_init__(self) -> None:
        ensure(
            _MIN_SESSION_RATING <= self.value <= _MAX_SESSION_RATING,
            f"session rating must be between {_MIN_SESSION_RATING} and "
            f"{_MAX_SESSION_RATING}, got {self.value}",
        )


@dataclass(frozen=True)
class CompletionPercentage(ValueObject):
    """How much of the planned session was actually completed, 0-100.

    Caller-supplied at `WorkoutSession.complete()`/`abandon()` rather than
    derived, the same reasoning
    `app.domain.workout.value_objects.WorkoutDuration` documents: deriving
    this would need per-exercise-set completion tracking
    (`ExerciseSet`/`LoggedExercise`), which this increment explicitly does
    not build.
    """

    value: float

    def __post_init__(self) -> None:
        ensure(
            _MIN_COMPLETION_PERCENTAGE <= self.value <= _MAX_COMPLETION_PERCENTAGE,
            f"completion percentage must be between {_MIN_COMPLETION_PERCENTAGE} and "
            f"{_MAX_COMPLETION_PERCENTAGE}, got {self.value}",
        )
