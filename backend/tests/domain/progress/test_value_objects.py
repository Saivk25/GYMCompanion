"""Tests for app/domain/progress/value_objects.py."""

from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from app.domain.progress.value_objects import (
    ArmMeasurement,
    BodyFatPercentage,
    BodyWeight,
    CalfMeasurement,
    ChestMeasurement,
    HipMeasurement,
    LeanBodyMass,
    MuscleMass,
    NeckMeasurement,
    ProgressDate,
    ProgressNotes,
    ThighMeasurement,
    WaistMeasurement,
)
from app.domain.shared_kernel.errors import DomainInvariantViolationError

# --- ProgressDate ---


@pytest.mark.unit
def test_progress_date_wraps_a_date() -> None:
    assert ProgressDate(date(2026, 1, 1)).value == date(2026, 1, 1)


@pytest.mark.unit
def test_progress_date_is_immutable() -> None:
    progress_date = ProgressDate(date(2026, 1, 1))
    with pytest.raises(FrozenInstanceError):
        progress_date.value = date(2026, 1, 2)  # type: ignore[misc]


@pytest.mark.unit
def test_progress_date_equality_is_by_value() -> None:
    assert ProgressDate(date(2026, 1, 1)) == ProgressDate(date(2026, 1, 1))
    assert ProgressDate(date(2026, 1, 1)) != ProgressDate(date(2026, 1, 2))


# --- BodyWeight ---


@pytest.mark.unit
@pytest.mark.parametrize("value", [0.1, 70.0, 150.0])
def test_body_weight_accepts_positive_values(value: float) -> None:
    assert BodyWeight(value).value == value


@pytest.mark.unit
@pytest.mark.parametrize("value", [0.0, -1.0])
def test_body_weight_rejects_non_positive_values(value: float) -> None:
    with pytest.raises(DomainInvariantViolationError, match="must be positive"):
        BodyWeight(value)


@pytest.mark.unit
def test_body_weight_is_immutable() -> None:
    weight = BodyWeight(70.0)
    with pytest.raises(FrozenInstanceError):
        weight.value = 71.0  # type: ignore[misc]


# --- BodyFatPercentage ---


@pytest.mark.unit
@pytest.mark.parametrize("value", [0.0, 20.0, 100.0])
def test_body_fat_percentage_accepts_values_within_bounds(value: float) -> None:
    assert BodyFatPercentage(value).value == value


@pytest.mark.unit
@pytest.mark.parametrize("value", [-0.1, 100.1])
def test_body_fat_percentage_rejects_values_outside_bounds(value: float) -> None:
    with pytest.raises(DomainInvariantViolationError, match=r"must be between 0.0 and 100.0"):
        BodyFatPercentage(value)


@pytest.mark.unit
def test_body_fat_percentage_is_immutable() -> None:
    body_fat = BodyFatPercentage(20.0)
    with pytest.raises(FrozenInstanceError):
        body_fat.value = 25.0  # type: ignore[misc]


# --- LeanBodyMass / MuscleMass and the seven tape measurements: same
# "must be positive" shape as BodyWeight, exercised generically below. ---

_POSITIVE_MEASUREMENT_TYPES = [
    LeanBodyMass,
    MuscleMass,
    WaistMeasurement,
    ChestMeasurement,
    HipMeasurement,
    ArmMeasurement,
    ThighMeasurement,
    CalfMeasurement,
    NeckMeasurement,
]


@pytest.mark.unit
@pytest.mark.parametrize("measurement_type", _POSITIVE_MEASUREMENT_TYPES)
@pytest.mark.parametrize("value", [0.1, 50.0])
def test_positive_measurement_types_accept_positive_values(
    measurement_type: type, value: float
) -> None:
    assert measurement_type(value).value == value


@pytest.mark.unit
@pytest.mark.parametrize("measurement_type", _POSITIVE_MEASUREMENT_TYPES)
@pytest.mark.parametrize("value", [0.0, -1.0])
def test_positive_measurement_types_reject_non_positive_values(
    measurement_type: type, value: float
) -> None:
    with pytest.raises(DomainInvariantViolationError, match="must be positive"):
        measurement_type(value)


@pytest.mark.unit
@pytest.mark.parametrize("measurement_type", _POSITIVE_MEASUREMENT_TYPES)
def test_positive_measurement_types_are_immutable(measurement_type: type) -> None:
    instance = measurement_type(50.0)
    with pytest.raises(FrozenInstanceError):
        instance.value = 60.0


@pytest.mark.unit
def test_positive_measurement_types_are_all_distinct() -> None:
    """Primitive-obsession guard: a `WaistMeasurement` must not be
    accidentally interchangeable with a `ChestMeasurement` even though
    both wrap "a positive float"."""
    assert len(set(_POSITIVE_MEASUREMENT_TYPES)) == len(_POSITIVE_MEASUREMENT_TYPES)
    assert WaistMeasurement(50.0) != ChestMeasurement(50.0)  # type: ignore[comparison-overlap]


# --- ProgressNotes ---


@pytest.mark.unit
def test_progress_notes_defaults_to_empty() -> None:
    assert ProgressNotes().value == ""


@pytest.mark.unit
def test_progress_notes_accepts_an_explicitly_empty_value() -> None:
    assert ProgressNotes("").value == ""


@pytest.mark.unit
def test_progress_notes_accepts_a_non_empty_value() -> None:
    assert ProgressNotes("Measured fasted.").value == "Measured fasted."


@pytest.mark.unit
def test_progress_notes_rejects_an_overly_long_value() -> None:
    with pytest.raises(DomainInvariantViolationError, match="at most 2000 characters"):
        ProgressNotes("x" * 2001)


@pytest.mark.unit
def test_progress_notes_is_immutable() -> None:
    notes = ProgressNotes("Felt good.")
    with pytest.raises(FrozenInstanceError):
        notes.value = "Changed"  # type: ignore[misc]
