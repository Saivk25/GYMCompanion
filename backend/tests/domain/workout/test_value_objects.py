"""Tests for app/domain/workout/value_objects.py."""

from dataclasses import FrozenInstanceError
from datetime import date, timedelta

import pytest

from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.workout.value_objects import (
    WorkoutDate,
    WorkoutDuration,
    WorkoutGoal,
    WorkoutName,
    WorkoutNotes,
)

# --- WorkoutName ---


@pytest.mark.unit
def test_workout_name_accepts_a_non_empty_value() -> None:
    assert WorkoutName("Push Day").value == "Push Day"


@pytest.mark.unit
def test_workout_name_rejects_blank_values() -> None:
    with pytest.raises(DomainInvariantViolationError, match="workout name must not be empty"):
        WorkoutName("   ")


@pytest.mark.unit
def test_workout_name_rejects_an_overly_long_value() -> None:
    with pytest.raises(DomainInvariantViolationError, match="at most 200 characters"):
        WorkoutName("x" * 201)


@pytest.mark.unit
def test_workout_name_is_immutable() -> None:
    name = WorkoutName("Push Day")
    with pytest.raises(FrozenInstanceError):
        name.value = "Pull Day"  # type: ignore[misc]


# --- WorkoutGoal ---


@pytest.mark.unit
def test_workout_goal_accepts_a_non_empty_value() -> None:
    assert WorkoutGoal("upper body strength").value == "upper body strength"


@pytest.mark.unit
def test_workout_goal_rejects_blank_values() -> None:
    with pytest.raises(DomainInvariantViolationError, match="workout goal must not be empty"):
        WorkoutGoal("")


@pytest.mark.unit
def test_workout_goal_rejects_an_overly_long_value() -> None:
    with pytest.raises(DomainInvariantViolationError, match="at most 200 characters"):
        WorkoutGoal("x" * 201)


# --- WorkoutNotes ---


@pytest.mark.unit
def test_workout_notes_accepts_a_non_empty_value() -> None:
    assert WorkoutNotes("Felt strong today").value == "Felt strong today"


@pytest.mark.unit
def test_workout_notes_rejects_blank_values() -> None:
    with pytest.raises(DomainInvariantViolationError, match="workout notes must not be empty"):
        WorkoutNotes("")


@pytest.mark.unit
def test_workout_notes_rejects_an_overly_long_value() -> None:
    with pytest.raises(DomainInvariantViolationError, match="at most 2000 characters"):
        WorkoutNotes("x" * 2001)


# --- WorkoutDuration ---


@pytest.mark.unit
def test_workout_duration_accepts_a_positive_timedelta() -> None:
    duration = WorkoutDuration(timedelta(minutes=45))
    assert duration.value == timedelta(minutes=45)


@pytest.mark.unit
def test_workout_duration_accepts_exactly_zero() -> None:
    """ "Cannot be negative" allows zero — this rule rejects negative
    durations specifically, not short ones."""
    duration = WorkoutDuration(timedelta(0))
    assert duration.value == timedelta(0)


@pytest.mark.unit
def test_workout_duration_rejects_a_negative_timedelta() -> None:
    with pytest.raises(DomainInvariantViolationError, match="must not be negative"):
        WorkoutDuration(timedelta(minutes=-1))


@pytest.mark.unit
def test_workout_duration_is_immutable() -> None:
    duration = WorkoutDuration(timedelta(minutes=45))
    with pytest.raises(FrozenInstanceError):
        duration.value = timedelta(minutes=50)  # type: ignore[misc]


# --- WorkoutDate ---


@pytest.mark.unit
def test_workout_date_wraps_a_date() -> None:
    assert WorkoutDate(date(2026, 1, 1)).value == date(2026, 1, 1)


@pytest.mark.unit
def test_workout_date_is_immutable() -> None:
    workout_date = WorkoutDate(date(2026, 1, 1))
    with pytest.raises(FrozenInstanceError):
        workout_date.value = date(2026, 1, 2)  # type: ignore[misc]


@pytest.mark.unit
def test_workout_date_equality_is_by_value() -> None:
    assert WorkoutDate(date(2026, 1, 1)) == WorkoutDate(date(2026, 1, 1))
    assert WorkoutDate(date(2026, 1, 1)) != WorkoutDate(date(2026, 1, 2))
