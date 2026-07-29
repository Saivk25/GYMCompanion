"""Immutable value objects owned by the Progress aggregate.

Every type here is a `ValueObject` subclass (`app.domain.shared_kernel`):
no identity, replaced wholesale on change, validated once at construction —
the same discipline every other aggregate's value objects follow.

Every measurement below is deliberately its own distinct type
(`WaistMeasurement` is not just a `float`, and is not interchangeable with
`ChestMeasurement` even though both are "a positive number") — the same
"primitive obsession" reasoning `app.domain.shared_kernel.identifiers`
documents for typed ids, applied to measurements instead. A caller passing
a chest measurement where a waist measurement is expected is a type error
mypy catches, not a silent unit-confusion bug.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.domain.shared_kernel.validation import ensure, ensure_positive
from app.domain.shared_kernel.value_object import ValueObject

_MIN_BODY_FAT_PERCENTAGE = 0.0
_MAX_BODY_FAT_PERCENTAGE = 100.0
_MAX_PROGRESS_NOTES_LENGTH = 2000


@dataclass(frozen=True)
class ProgressDate(ValueObject):
    """The calendar date this progress check-in was recorded for — a
    `datetime.date`, not a `datetime`, the same reasoning
    `app.domain.workout_session.value_objects.SessionDate` documents: a
    check-in belongs to a day, not an instant. "Progress date required" is
    enforced by `Progress` requiring one at construction, not by any extra
    validation here — every `date` value is a valid `ProgressDate`.
    """

    value: date


@dataclass(frozen=True)
class BodyWeight(ValueObject):
    """Total body weight, in whatever `MeasurementUnit` the owning
    `Progress` record specifies. "Body weight must be positive."
    """

    value: float

    def __post_init__(self) -> None:
        ensure_positive(self.value, "body_weight")


@dataclass(frozen=True)
class BodyFatPercentage(ValueObject):
    """Body fat as a percentage of total body weight. "Body fat percentage
    between 0 and 100" — inclusive at both ends, the same bound shape
    `app.domain.workout_session.value_objects.CompletionPercentage`
    already uses for a 0-100 value.
    """

    value: float

    def __post_init__(self) -> None:
        ensure(
            _MIN_BODY_FAT_PERCENTAGE <= self.value <= _MAX_BODY_FAT_PERCENTAGE,
            f"body fat percentage must be between {_MIN_BODY_FAT_PERCENTAGE} and "
            f"{_MAX_BODY_FAT_PERCENTAGE}, got {self.value}",
        )


@dataclass(frozen=True)
class LeanBodyMass(ValueObject):
    """Body mass excluding fat mass, in the record's `MeasurementUnit`.
    Grouped with `BodyWeight`/`BodyFatPercentage`/`MuscleMass` under
    `Progress.update_body_composition()` and the `BodyCompositionUpdated`
    event. "Measurements must be positive" applies here the same as every
    other numeric field on this aggregate besides `BodyFatPercentage`
    (which has its own 0-100 bound).
    """

    value: float

    def __post_init__(self) -> None:
        ensure_positive(self.value, "lean_body_mass")


@dataclass(frozen=True)
class MuscleMass(ValueObject):
    """Skeletal muscle mass, in the record's `MeasurementUnit`. "Measurements
    must be positive."
    """

    value: float

    def __post_init__(self) -> None:
        ensure_positive(self.value, "muscle_mass")


@dataclass(frozen=True)
class WaistMeasurement(ValueObject):
    """Waist circumference, in the record's `MeasurementUnit`. "Measurements
    must be positive." One of the Bible's own named `Measurement` fields
    (Section 4.10, Table 13).
    """

    value: float

    def __post_init__(self) -> None:
        ensure_positive(self.value, "waist_measurement")


@dataclass(frozen=True)
class ChestMeasurement(ValueObject):
    """Chest circumference, in the record's `MeasurementUnit`. "Measurements
    must be positive." One of the Bible's own named `Measurement` fields
    (Section 4.10, Table 13).
    """

    value: float

    def __post_init__(self) -> None:
        ensure_positive(self.value, "chest_measurement")


@dataclass(frozen=True)
class HipMeasurement(ValueObject):
    """Hip circumference, in the record's `MeasurementUnit`. "Measurements
    must be positive." One of the Bible's own named `Measurement` fields
    (Section 4.10, Table 13).
    """

    value: float

    def __post_init__(self) -> None:
        ensure_positive(self.value, "hip_measurement")


@dataclass(frozen=True)
class ArmMeasurement(ValueObject):
    """Arm circumference, in the record's `MeasurementUnit`. "Measurements
    must be positive." One of the Bible's own named `Measurement` fields
    (Section 4.10, Table 13).
    """

    value: float

    def __post_init__(self) -> None:
        ensure_positive(self.value, "arm_measurement")


@dataclass(frozen=True)
class ThighMeasurement(ValueObject):
    """Thigh circumference, in the record's `MeasurementUnit`. "Measurements
    must be positive." One of the Bible's own named `Measurement` fields
    (Section 4.10, Table 13).
    """

    value: float

    def __post_init__(self) -> None:
        ensure_positive(self.value, "thigh_measurement")


@dataclass(frozen=True)
class CalfMeasurement(ValueObject):
    """Calf circumference, in the record's `MeasurementUnit`. "Measurements
    must be positive." Not one of the Bible's own named `Measurement`
    fields — this increment's own addition, alongside `NeckMeasurement`,
    rounding out the common tape-measurement sites beyond the Bible's
    weight/waist/hip/chest/arm/thigh list.
    """

    value: float

    def __post_init__(self) -> None:
        ensure_positive(self.value, "calf_measurement")


@dataclass(frozen=True)
class NeckMeasurement(ValueObject):
    """Neck circumference, in the record's `MeasurementUnit`. "Measurements
    must be positive." Not one of the Bible's own named `Measurement`
    fields — see `CalfMeasurement`'s docstring for why it's included
    anyway.
    """

    value: float

    def __post_init__(self) -> None:
        ensure_positive(self.value, "neck_measurement")


@dataclass(frozen=True)
class ProgressNotes(ValueObject):
    """Free-text notes on this check-in (e.g. "measured first thing in the
    morning, fasted"). "Notes may be empty" — the same "empty is a valid
    value, not `None`" discipline as
    `app.domain.workout_session.value_objects.SessionNotes` and
    `app.domain.workout_session.exercise_performance.PerformanceNotes`:
    `Progress.notes` is never `None`, only ever a `ProgressNotes` that may
    happen to be empty.
    """

    value: str = ""

    def __post_init__(self) -> None:
        ensure(
            len(self.value) <= _MAX_PROGRESS_NOTES_LENGTH,
            f"progress notes must be at most {_MAX_PROGRESS_NOTES_LENGTH} characters, "
            f"got {len(self.value)}",
        )
