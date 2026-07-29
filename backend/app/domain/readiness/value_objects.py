"""Immutable value objects owned by the Readiness aggregate.

Every type here is a `ValueObject` subclass (`app.domain.shared_kernel`):
no identity, replaced wholesale on change, validated once at construction —
the same discipline every other aggregate's value objects follow.

`SleepQuality`/`EnergyLevel`/`StressLevel`/`SorenessLevel` all share the
1-10 bound this increment chose for the task's "bounded (for example
1-10)" rule — the same Borg CR10-style reasoning
`app.domain.workout_session.value_objects.SessionRating` and
`app.domain.workout_session.exercise_set.SetRPE` already document for a
subjective 1-10 scale. Each is still its own distinct type, not a shared
"bounded int" wrapper — a caller passing `StressLevel` where
`EnergyLevel` is expected is a type error mypy catches, not a silent
mix-up between two different subjective ratings.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from app.domain.shared_kernel.validation import ensure, ensure_positive
from app.domain.shared_kernel.value_object import ValueObject

_MIN_SUBJECTIVE_RATING = 1
_MAX_SUBJECTIVE_RATING = 10
_MAX_RECOVERY_NOTES_LENGTH = 2000


@dataclass(frozen=True)
class ReadinessDate(ValueObject):
    """The calendar date this readiness check-in was recorded for — a
    `datetime.date`, not a `datetime`, the same reasoning
    `app.domain.progress.value_objects.ProgressDate` documents. "Readiness
    date required" is enforced by `Readiness` requiring one at
    construction, not by any extra validation here.
    """

    value: date


@dataclass(frozen=True)
class SleepDuration(ValueObject):
    """How long the user slept, as a `datetime.timedelta`. "Sleep duration
    >= 0" — zero is allowed (a reported all-nighter), the same "must not
    be negative" shape
    `app.domain.workout.value_objects.WorkoutDuration` uses, not the
    stricter "must be positive"
    `app.domain.workout_session.value_objects.SessionDuration` uses.
    """

    value: timedelta

    def __post_init__(self) -> None:
        ensure(
            self.value >= timedelta(0),
            f"sleep duration must not be negative, got {self.value}",
        )


@dataclass(frozen=True)
class SleepQuality(ValueObject):
    """Self-reported sleep quality, 1-10. See the module-level comment
    above for why 1-10."""

    value: int

    def __post_init__(self) -> None:
        ensure(
            _MIN_SUBJECTIVE_RATING <= self.value <= _MAX_SUBJECTIVE_RATING,
            f"sleep quality must be between {_MIN_SUBJECTIVE_RATING} and "
            f"{_MAX_SUBJECTIVE_RATING}, got {self.value}",
        )


@dataclass(frozen=True)
class EnergyLevel(ValueObject):
    """Self-reported energy level, 1-10. See the module-level comment
    above for why 1-10."""

    value: int

    def __post_init__(self) -> None:
        ensure(
            _MIN_SUBJECTIVE_RATING <= self.value <= _MAX_SUBJECTIVE_RATING,
            f"energy level must be between {_MIN_SUBJECTIVE_RATING} and "
            f"{_MAX_SUBJECTIVE_RATING}, got {self.value}",
        )


@dataclass(frozen=True)
class StressLevel(ValueObject):
    """Self-reported stress level, 1-10. One of the Bible's own named
    `ReadinessCheckIn` fields (Section 4.8, Table 11: `stress_level`). See
    the module-level comment above for why 1-10.
    """

    value: int

    def __post_init__(self) -> None:
        ensure(
            _MIN_SUBJECTIVE_RATING <= self.value <= _MAX_SUBJECTIVE_RATING,
            f"stress level must be between {_MIN_SUBJECTIVE_RATING} and "
            f"{_MAX_SUBJECTIVE_RATING}, got {self.value}",
        )


@dataclass(frozen=True)
class SorenessLevel(ValueObject):
    """Self-reported muscle soreness, 1-10. One of the Bible's own named
    `ReadinessCheckIn` fields (Section 4.8, Table 11: `soreness`). See the
    module-level comment above for why 1-10.
    """

    value: int

    def __post_init__(self) -> None:
        ensure(
            _MIN_SUBJECTIVE_RATING <= self.value <= _MAX_SUBJECTIVE_RATING,
            f"soreness level must be between {_MIN_SUBJECTIVE_RATING} and "
            f"{_MAX_SUBJECTIVE_RATING}, got {self.value}",
        )


@dataclass(frozen=True)
class RestingHeartRate(ValueObject):
    """Resting heart rate, in beats per minute. "Heart rate positive" —
    strictly greater than zero, via the shared kernel's `ensure_positive`
    (a heart rate of zero does not describe a living person). Not one of
    the Bible's own named `ReadinessCheckIn` fields — this increment's own
    addition, alongside `HeartRateVariability`, the common wearable-derived
    metrics beyond the Bible's self-reported sleep/stress/soreness list.
    """

    value: float

    def __post_init__(self) -> None:
        ensure_positive(self.value, "resting_heart_rate")


@dataclass(frozen=True)
class HeartRateVariability(ValueObject):
    """Heart rate variability, in milliseconds (a common RMSSD-style
    unit). "HRV positive." Not one of the Bible's own named
    `ReadinessCheckIn` fields — see `RestingHeartRate`'s docstring for why
    it's included anyway.
    """

    value: float

    def __post_init__(self) -> None:
        ensure_positive(self.value, "heart_rate_variability")


@dataclass(frozen=True)
class RecoveryNotes(ValueObject):
    """Free-text notes on this check-in. "Notes may be empty" — the same
    "empty is a valid value, not `None`" discipline as
    `app.domain.progress.value_objects.ProgressNotes` and
    `app.domain.nutrition.value_objects.MealNotes`: `Readiness.notes` is
    never `None`, only ever a `RecoveryNotes` that may happen to be empty.
    """

    value: str = ""

    def __post_init__(self) -> None:
        ensure(
            len(self.value) <= _MAX_RECOVERY_NOTES_LENGTH,
            f"recovery notes must be at most {_MAX_RECOVERY_NOTES_LENGTH} characters, "
            f"got {len(self.value)}",
        )
