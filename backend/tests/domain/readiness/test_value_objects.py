"""Tests for app/domain/readiness/value_objects.py."""

from dataclasses import FrozenInstanceError
from datetime import date, timedelta

import pytest

from app.domain.readiness.value_objects import (
    EnergyLevel,
    HeartRateVariability,
    ReadinessDate,
    RecoveryNotes,
    RestingHeartRate,
    SleepDuration,
    SleepQuality,
    SorenessLevel,
    StressLevel,
)
from app.domain.shared_kernel.errors import DomainInvariantViolationError

# --- ReadinessDate ---


@pytest.mark.unit
def test_readiness_date_wraps_a_date() -> None:
    assert ReadinessDate(date(2026, 1, 1)).value == date(2026, 1, 1)


@pytest.mark.unit
def test_readiness_date_is_immutable() -> None:
    readiness_date = ReadinessDate(date(2026, 1, 1))
    with pytest.raises(FrozenInstanceError):
        readiness_date.value = date(2026, 1, 2)  # type: ignore[misc]


@pytest.mark.unit
def test_readiness_date_equality_is_by_value() -> None:
    assert ReadinessDate(date(2026, 1, 1)) == ReadinessDate(date(2026, 1, 1))
    assert ReadinessDate(date(2026, 1, 1)) != ReadinessDate(date(2026, 1, 2))


# --- SleepDuration ---


@pytest.mark.unit
def test_sleep_duration_accepts_zero() -> None:
    """Zero is allowed — a reported all-nighter — unlike SessionDuration's
    strictly-positive bound."""
    assert SleepDuration(timedelta(0)).value == timedelta(0)


@pytest.mark.unit
def test_sleep_duration_accepts_a_positive_timedelta() -> None:
    duration = SleepDuration(timedelta(hours=7, minutes=30))
    assert duration.value == timedelta(hours=7, minutes=30)


@pytest.mark.unit
def test_sleep_duration_rejects_a_negative_timedelta() -> None:
    with pytest.raises(DomainInvariantViolationError, match="must not be negative"):
        SleepDuration(timedelta(hours=-1))


@pytest.mark.unit
def test_sleep_duration_is_immutable() -> None:
    duration = SleepDuration(timedelta(hours=7))
    with pytest.raises(FrozenInstanceError):
        duration.value = timedelta(hours=8)  # type: ignore[misc]


# --- SleepQuality / EnergyLevel / StressLevel / SorenessLevel: all share
# the same 1-10 bound, exercised generically below. ---

_SUBJECTIVE_RATING_TYPES = [SleepQuality, EnergyLevel, StressLevel, SorenessLevel]


@pytest.mark.unit
@pytest.mark.parametrize("rating_type", _SUBJECTIVE_RATING_TYPES)
@pytest.mark.parametrize("value", [1, 5, 10])
def test_subjective_rating_types_accept_values_within_bounds(rating_type: type, value: int) -> None:
    assert rating_type(value).value == value


@pytest.mark.unit
@pytest.mark.parametrize("rating_type", _SUBJECTIVE_RATING_TYPES)
@pytest.mark.parametrize("value", [0, -1, 11])
def test_subjective_rating_types_reject_values_outside_bounds(
    rating_type: type, value: int
) -> None:
    with pytest.raises(DomainInvariantViolationError, match="must be between 1 and 10"):
        rating_type(value)


@pytest.mark.unit
@pytest.mark.parametrize("rating_type", _SUBJECTIVE_RATING_TYPES)
def test_subjective_rating_types_are_immutable(rating_type: type) -> None:
    instance = rating_type(5)
    with pytest.raises(FrozenInstanceError):
        instance.value = 6


@pytest.mark.unit
def test_subjective_rating_types_are_all_distinct() -> None:
    """Primitive-obsession guard: a `StressLevel` must not be accidentally
    interchangeable with an `EnergyLevel` even though both wrap "an int
    1-10"."""
    assert len(set(_SUBJECTIVE_RATING_TYPES)) == len(_SUBJECTIVE_RATING_TYPES)
    assert StressLevel(5) != EnergyLevel(5)  # type: ignore[comparison-overlap]


# --- RestingHeartRate / HeartRateVariability: both strictly positive. ---

_POSITIVE_TYPES = [RestingHeartRate, HeartRateVariability]


@pytest.mark.unit
@pytest.mark.parametrize("value_type", _POSITIVE_TYPES)
@pytest.mark.parametrize("value", [0.1, 60.0, 120.0])
def test_positive_types_accept_positive_values(value_type: type, value: float) -> None:
    assert value_type(value).value == value


@pytest.mark.unit
@pytest.mark.parametrize("value_type", _POSITIVE_TYPES)
@pytest.mark.parametrize("value", [0.0, -1.0])
def test_positive_types_reject_non_positive_values(value_type: type, value: float) -> None:
    with pytest.raises(DomainInvariantViolationError, match="must be positive"):
        value_type(value)


@pytest.mark.unit
@pytest.mark.parametrize("value_type", _POSITIVE_TYPES)
def test_positive_types_are_immutable(value_type: type) -> None:
    instance = value_type(60.0)
    with pytest.raises(FrozenInstanceError):
        instance.value = 65.0


@pytest.mark.unit
def test_positive_types_are_distinct() -> None:
    assert RestingHeartRate(60.0) != HeartRateVariability(60.0)  # type: ignore[comparison-overlap]


# --- RecoveryNotes ---


@pytest.mark.unit
def test_recovery_notes_defaults_to_empty() -> None:
    assert RecoveryNotes().value == ""


@pytest.mark.unit
def test_recovery_notes_accepts_an_explicitly_empty_value() -> None:
    assert RecoveryNotes("").value == ""


@pytest.mark.unit
def test_recovery_notes_accepts_a_non_empty_value() -> None:
    assert RecoveryNotes("Slept poorly.").value == "Slept poorly."


@pytest.mark.unit
def test_recovery_notes_rejects_an_overly_long_value() -> None:
    with pytest.raises(DomainInvariantViolationError, match="at most 2000 characters"):
        RecoveryNotes("x" * 2001)


@pytest.mark.unit
def test_recovery_notes_is_immutable() -> None:
    notes = RecoveryNotes("Felt good.")
    with pytest.raises(FrozenInstanceError):
        notes.value = "Changed"  # type: ignore[misc]
