"""Immutable value objects owned by the Goal aggregate.

Every type here is a `ValueObject` subclass (`app.domain.shared_kernel`):
no identity, replaced wholesale on change, validated once at construction —
the same discipline every other aggregate's value objects follow.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.domain.shared_kernel.validation import ensure, ensure_not_empty, ensure_positive
from app.domain.shared_kernel.value_object import ValueObject

_MAX_GOAL_NAME_LENGTH = 200
_MAX_GOAL_DESCRIPTION_LENGTH = 2000
_MAX_GOAL_NOTES_LENGTH = 2000
_MIN_BODY_FAT_PERCENTAGE = 0.0
_MAX_BODY_FAT_PERCENTAGE = 100.0

# "Priority must be within defined bounds" names no specific range. 1-5
# (five discrete rank tiers) is this increment's own choice, deliberately
# distinct in shape from the 1-10 subjective-feeling scales used elsewhere
# (`app.domain.workout_session.value_objects.SessionRating`,
# `app.domain.workout_session.exercise_set.SetRPE`,
# `app.domain.readiness.value_objects.SleepQuality` and siblings) — a
# priority rank is a small, discrete ordering, not a continuous subjective
# rating, so a coarser bound reads more honestly.
_MIN_PRIORITY = 1
_MAX_PRIORITY = 5


@dataclass(frozen=True)
class GoalName(ValueObject):
    """What the user calls this goal, e.g. `GoalName("Lose 5kg by June")`.
    "Goal name required" — enforced by `Goal` requiring one at
    construction (the type isn't `Optional`) and by this value object
    rejecting an empty string, the same two-layer enforcement
    `app.domain.workout.value_objects.WorkoutName` uses.
    """

    value: str

    def __post_init__(self) -> None:
        ensure_not_empty(self.value, "goal name")
        ensure(
            len(self.value) <= _MAX_GOAL_NAME_LENGTH,
            f"goal name must be at most {_MAX_GOAL_NAME_LENGTH} characters, got {len(self.value)}",
        )


@dataclass(frozen=True)
class GoalDescription(ValueObject):
    """A longer free-text description of the goal. Optional on `Goal`
    (`GoalDescription | None`) — if there's nothing to say, `Goal.
    description` is `None`, not a `GoalDescription` holding an empty
    string, the same "two ways to represent nothing" avoidance
    `app.domain.workout.value_objects.WorkoutGoal` documents.
    """

    value: str

    def __post_init__(self) -> None:
        ensure_not_empty(self.value, "goal description")
        ensure(
            len(self.value) <= _MAX_GOAL_DESCRIPTION_LENGTH,
            f"goal description must be at most {_MAX_GOAL_DESCRIPTION_LENGTH} "
            f"characters, got {len(self.value)}",
        )


@dataclass(frozen=True)
class TargetWeight(ValueObject):
    """The body weight this goal targets, in whatever unit the caller has
    agreed with the user (this increment carries no `MeasurementUnit`
    field on `Goal` — see the class docstring in `goal.py`). "Target
    values must be valid" — for a weight, that means strictly positive,
    the same bound
    `app.domain.progress.value_objects.BodyWeight` already uses.
    """

    value: float

    def __post_init__(self) -> None:
        ensure_positive(self.value, "target_weight")


@dataclass(frozen=True)
class TargetBodyFat(ValueObject):
    """The body fat percentage this goal targets. "Target values must be
    valid" — for a percentage, that means 0-100 inclusive, the same bound
    `app.domain.progress.value_objects.BodyFatPercentage` already uses.
    """

    value: float

    def __post_init__(self) -> None:
        ensure(
            _MIN_BODY_FAT_PERCENTAGE <= self.value <= _MAX_BODY_FAT_PERCENTAGE,
            f"target body fat must be between {_MIN_BODY_FAT_PERCENTAGE} and "
            f"{_MAX_BODY_FAT_PERCENTAGE}, got {self.value}",
        )


@dataclass(frozen=True)
class TargetStrength(ValueObject):
    """A target load for a lift this goal is measured against (e.g. "squat
    100kg"), deliberately unit- and exercise-agnostic — this increment has
    no field tying a `Goal` to a specific `ExerciseId` or unit, only the
    raw target number. "Target values must be valid" — for a load, that
    means strictly positive, via the shared kernel's `ensure_positive`.
    """

    value: float

    def __post_init__(self) -> None:
        ensure_positive(self.value, "target_strength")


@dataclass(frozen=True)
class TargetDate(ValueObject):
    """The date this goal targets completion by — a `datetime.date`, not a
    `datetime`, the same reasoning every other `*Date` value object in
    this codebase documents. "Target date required" is enforced by `Goal`
    requiring one at construction, not by any extra validation here — every
    `date` value is a valid `TargetDate`. The Domain Model & Decision
    Engine Bible is explicit that a target date, when present, "is never
    treated as a guarantee" (Section 4.4) — that framing belongs to
    whatever future component narrates or forecasts against this goal, not
    to this value object, which only wraps the date itself.
    """

    value: date


@dataclass(frozen=True)
class Priority(ValueObject):
    """This goal's rank relative to a user's other goals, 1-5 (1 =
    highest). See the module-level comment above for why 1-5 rather than
    the 1-10 scale used elsewhere in this codebase. Enforcing an actual
    ranking across a user's concurrent goals (the Bible's "Multiple Active
    goals require an explicit ranking", Section 7.4) is out of scope here
    — this value object only validates one goal's own priority is within
    bounds, the same "no cross-aggregate uniqueness at the domain layer"
    discipline `app.domain.readiness.readiness`'s module docstring
    documents for "one check-in per day".
    """

    value: int

    def __post_init__(self) -> None:
        ensure(
            _MIN_PRIORITY <= self.value <= _MAX_PRIORITY,
            f"priority must be between {_MIN_PRIORITY} and {_MAX_PRIORITY}, got {self.value}",
        )


@dataclass(frozen=True)
class GoalNotes(ValueObject):
    """Free-text, ongoing notes on progress toward this goal — distinct
    from `GoalDescription` (what the goal *is*): "Notes may be empty" is
    not stated for `Goal` specifically in this task's Rules, but every
    other `*Notes` value object in this codebase treats empty as a valid,
    always-present value rather than relying on `None`
    (`app.domain.progress.value_objects.ProgressNotes`,
    `app.domain.nutrition.value_objects.MealNotes`,
    `app.domain.readiness.value_objects.RecoveryNotes`) — this one follows
    the same convention for consistency.
    """

    value: str = ""

    def __post_init__(self) -> None:
        ensure(
            len(self.value) <= _MAX_GOAL_NOTES_LENGTH,
            f"goal notes must be at most {_MAX_GOAL_NOTES_LENGTH} characters, "
            f"got {len(self.value)}",
        )
