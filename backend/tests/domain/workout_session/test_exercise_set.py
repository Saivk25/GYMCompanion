"""Tests for app/domain/workout_session/exercise_set.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.workout_session.exercise_set import (
    ExerciseSet,
    SetNumber,
    SetReps,
    SetRPE,
    SetWeight,
)
from tests.domain.workout_session.factories import an_exercise_set

# --- SetNumber ---


@pytest.mark.unit
@pytest.mark.parametrize("value", [1, 2, 100])
def test_set_number_accepts_positive_values(value: int) -> None:
    assert SetNumber(value).value == value


@pytest.mark.unit
@pytest.mark.parametrize("value", [0, -1])
def test_set_number_rejects_non_positive_values(value: int) -> None:
    with pytest.raises(DomainInvariantViolationError, match="must be positive"):
        SetNumber(value)


@pytest.mark.unit
def test_set_number_is_immutable() -> None:
    set_number = SetNumber(1)
    with pytest.raises(FrozenInstanceError):
        set_number.value = 2  # type: ignore[misc]


# --- SetWeight ---


@pytest.mark.unit
@pytest.mark.parametrize("value", [0.0, 20.0, 140.5])
def test_set_weight_accepts_zero_or_positive_values(value: float) -> None:
    """Zero is a legitimate bodyweight-exercise weight, not an error."""
    assert SetWeight(value).value == value


@pytest.mark.unit
def test_set_weight_rejects_a_negative_value() -> None:
    with pytest.raises(DomainInvariantViolationError, match="must not be negative"):
        SetWeight(-0.1)


@pytest.mark.unit
def test_set_weight_is_immutable() -> None:
    weight = SetWeight(100.0)
    with pytest.raises(FrozenInstanceError):
        weight.value = 90.0  # type: ignore[misc]


# --- SetReps ---


@pytest.mark.unit
@pytest.mark.parametrize("value", [1, 5, 50])
def test_set_reps_accepts_positive_values(value: int) -> None:
    assert SetReps(value).value == value


@pytest.mark.unit
@pytest.mark.parametrize("value", [0, -1])
def test_set_reps_rejects_non_positive_values(value: int) -> None:
    with pytest.raises(DomainInvariantViolationError, match="must be positive"):
        SetReps(value)


@pytest.mark.unit
def test_set_reps_is_immutable() -> None:
    reps = SetReps(5)
    with pytest.raises(FrozenInstanceError):
        reps.value = 6  # type: ignore[misc]


# --- SetRPE ---


@pytest.mark.unit
@pytest.mark.parametrize("value", [1, 5, 10])
def test_set_rpe_accepts_values_within_bounds(value: int) -> None:
    assert SetRPE(value).value == value


@pytest.mark.unit
@pytest.mark.parametrize("value", [0, -1, 11])
def test_set_rpe_rejects_values_outside_bounds(value: int) -> None:
    with pytest.raises(DomainInvariantViolationError, match="must be between 1 and 10"):
        SetRPE(value)


@pytest.mark.unit
def test_set_rpe_is_immutable() -> None:
    rpe = SetRPE(7)
    with pytest.raises(FrozenInstanceError):
        rpe.value = 8  # type: ignore[misc]


# --- ExerciseSet ---


@pytest.mark.unit
def test_exercise_set_defaults_to_not_completed() -> None:
    exercise_set = an_exercise_set()
    assert exercise_set.completed is False


@pytest.mark.unit
def test_exercise_set_exposes_the_fields_it_was_given() -> None:
    exercise_set = ExerciseSet(
        set_number=SetNumber(2),
        weight=SetWeight(80.0),
        reps=SetReps(8),
        rpe=SetRPE(6),
    )
    assert exercise_set.set_number == SetNumber(2)
    assert exercise_set.weight == SetWeight(80.0)
    assert exercise_set.reps == SetReps(8)
    assert exercise_set.rpe == SetRPE(6)


@pytest.mark.unit
def test_exercise_set_is_immutable() -> None:
    exercise_set = an_exercise_set()
    with pytest.raises(FrozenInstanceError):
        exercise_set.completed = True  # type: ignore[misc]


@pytest.mark.unit
def test_exercise_set_equality_is_by_value() -> None:
    assert an_exercise_set(set_number=1) == an_exercise_set(set_number=1)
    assert an_exercise_set(set_number=1) != an_exercise_set(set_number=2)


@pytest.mark.unit
def test_mark_completed_returns_a_new_instance_with_completed_true() -> None:
    original = an_exercise_set(completed=False)
    completed = original.mark_completed()
    assert completed.completed is True
    assert original.completed is False  # original untouched — immutability


@pytest.mark.unit
def test_mark_completed_preserves_every_other_field() -> None:
    original = an_exercise_set(set_number=3, weight=60.0, reps=10, rpe=9)
    completed = original.mark_completed()
    assert completed.set_number == original.set_number
    assert completed.weight == original.weight
    assert completed.reps == original.reps
    assert completed.rpe == original.rpe
