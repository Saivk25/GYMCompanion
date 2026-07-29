"""Tests for app/domain/goal/value_objects.py."""

from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from app.domain.goal.value_objects import (
    GoalDescription,
    GoalName,
    GoalNotes,
    Priority,
    TargetBodyFat,
    TargetDate,
    TargetStrength,
    TargetWeight,
)
from app.domain.shared_kernel.errors import DomainInvariantViolationError

# --- GoalName ---


@pytest.mark.unit
def test_goal_name_accepts_a_non_empty_value() -> None:
    assert GoalName("Lose 5kg by June").value == "Lose 5kg by June"


@pytest.mark.unit
def test_goal_name_rejects_an_empty_value() -> None:
    with pytest.raises(DomainInvariantViolationError, match="goal name must not be empty"):
        GoalName("")


@pytest.mark.unit
def test_goal_name_rejects_an_overly_long_value() -> None:
    with pytest.raises(DomainInvariantViolationError, match="at most 200 characters"):
        GoalName("x" * 201)


@pytest.mark.unit
def test_goal_name_accepts_the_boundary_length() -> None:
    assert GoalName("x" * 200).value == "x" * 200


@pytest.mark.unit
def test_goal_name_is_immutable() -> None:
    name = GoalName("Lose 5kg")
    with pytest.raises(FrozenInstanceError):
        name.value = "Changed"  # type: ignore[misc]


@pytest.mark.unit
def test_goal_name_equality_is_by_value() -> None:
    assert GoalName("Lose 5kg") == GoalName("Lose 5kg")
    assert GoalName("Lose 5kg") != GoalName("Gain muscle")


# --- GoalDescription ---


@pytest.mark.unit
def test_goal_description_accepts_a_non_empty_value() -> None:
    assert GoalDescription("A longer explanation.").value == "A longer explanation."


@pytest.mark.unit
def test_goal_description_rejects_an_empty_value() -> None:
    """`GoalDescription` is `Optional` on `Goal` — "nothing to say" is
    `None`, never an empty `GoalDescription`."""
    with pytest.raises(DomainInvariantViolationError, match="goal description must not be empty"):
        GoalDescription("")


@pytest.mark.unit
def test_goal_description_rejects_an_overly_long_value() -> None:
    with pytest.raises(DomainInvariantViolationError, match="at most 2000 characters"):
        GoalDescription("x" * 2001)


@pytest.mark.unit
def test_goal_description_is_immutable() -> None:
    description = GoalDescription("A goal.")
    with pytest.raises(FrozenInstanceError):
        description.value = "Changed"  # type: ignore[misc]


# --- TargetWeight ---


@pytest.mark.unit
def test_target_weight_accepts_a_positive_value() -> None:
    assert TargetWeight(70.0).value == 70.0


@pytest.mark.unit
def test_target_weight_rejects_zero() -> None:
    with pytest.raises(DomainInvariantViolationError, match="must be positive"):
        TargetWeight(0.0)


@pytest.mark.unit
def test_target_weight_rejects_a_negative_value() -> None:
    with pytest.raises(DomainInvariantViolationError, match="must be positive"):
        TargetWeight(-1.0)


@pytest.mark.unit
def test_target_weight_is_immutable() -> None:
    weight = TargetWeight(70.0)
    with pytest.raises(FrozenInstanceError):
        weight.value = 75.0  # type: ignore[misc]


# --- TargetBodyFat ---


@pytest.mark.unit
@pytest.mark.parametrize("value", [0.0, 15.0, 100.0])
def test_target_body_fat_accepts_values_within_bounds(value: float) -> None:
    assert TargetBodyFat(value).value == value


@pytest.mark.unit
@pytest.mark.parametrize("value", [-0.1, 100.1])
def test_target_body_fat_rejects_values_outside_bounds(value: float) -> None:
    with pytest.raises(DomainInvariantViolationError, match=r"must be between 0\.0 and 100\.0"):
        TargetBodyFat(value)


@pytest.mark.unit
def test_target_body_fat_is_immutable() -> None:
    body_fat = TargetBodyFat(15.0)
    with pytest.raises(FrozenInstanceError):
        body_fat.value = 20.0  # type: ignore[misc]


# --- TargetStrength ---


@pytest.mark.unit
def test_target_strength_accepts_a_positive_value() -> None:
    assert TargetStrength(100.0).value == 100.0


@pytest.mark.unit
def test_target_strength_rejects_zero() -> None:
    with pytest.raises(DomainInvariantViolationError, match="must be positive"):
        TargetStrength(0.0)


@pytest.mark.unit
def test_target_strength_rejects_a_negative_value() -> None:
    with pytest.raises(DomainInvariantViolationError, match="must be positive"):
        TargetStrength(-50.0)


@pytest.mark.unit
def test_target_strength_is_immutable() -> None:
    strength = TargetStrength(100.0)
    with pytest.raises(FrozenInstanceError):
        strength.value = 110.0  # type: ignore[misc]


@pytest.mark.unit
def test_target_weight_and_target_strength_are_distinct_types() -> None:
    """Primitive-obsession guard: both wrap "a positive float" but must not
    be interchangeable."""
    assert TargetWeight(100.0) != TargetStrength(100.0)  # type: ignore[comparison-overlap]


# --- TargetDate ---


@pytest.mark.unit
def test_target_date_wraps_a_date() -> None:
    assert TargetDate(date(2026, 6, 1)).value == date(2026, 6, 1)


@pytest.mark.unit
def test_target_date_is_immutable() -> None:
    target_date = TargetDate(date(2026, 6, 1))
    with pytest.raises(FrozenInstanceError):
        target_date.value = date(2026, 7, 1)  # type: ignore[misc]


@pytest.mark.unit
def test_target_date_equality_is_by_value() -> None:
    assert TargetDate(date(2026, 6, 1)) == TargetDate(date(2026, 6, 1))
    assert TargetDate(date(2026, 6, 1)) != TargetDate(date(2026, 7, 1))


@pytest.mark.unit
def test_target_date_accepts_a_date_in_the_past() -> None:
    """No "must be in the future" bound — the Bible is explicit a target
    date is "never treated as a guarantee"; that framing (and any
    freshness check) belongs elsewhere, not to this value object."""
    assert TargetDate(date(2000, 1, 1)).value == date(2000, 1, 1)


# --- Priority ---


@pytest.mark.unit
@pytest.mark.parametrize("value", [1, 3, 5])
def test_priority_accepts_values_within_bounds(value: int) -> None:
    assert Priority(value).value == value


@pytest.mark.unit
@pytest.mark.parametrize("value", [0, -1, 6])
def test_priority_rejects_values_outside_bounds(value: int) -> None:
    with pytest.raises(DomainInvariantViolationError, match="must be between 1 and 5"):
        Priority(value)


@pytest.mark.unit
def test_priority_is_immutable() -> None:
    priority = Priority(1)
    with pytest.raises(FrozenInstanceError):
        priority.value = 2  # type: ignore[misc]


# --- GoalNotes ---


@pytest.mark.unit
def test_goal_notes_defaults_to_empty() -> None:
    assert GoalNotes().value == ""


@pytest.mark.unit
def test_goal_notes_accepts_an_explicitly_empty_value() -> None:
    assert GoalNotes("").value == ""


@pytest.mark.unit
def test_goal_notes_accepts_a_non_empty_value() -> None:
    assert GoalNotes("Making good progress.").value == "Making good progress."


@pytest.mark.unit
def test_goal_notes_rejects_an_overly_long_value() -> None:
    with pytest.raises(DomainInvariantViolationError, match="at most 2000 characters"):
        GoalNotes("x" * 2001)


@pytest.mark.unit
def test_goal_notes_is_immutable() -> None:
    notes = GoalNotes("Some notes.")
    with pytest.raises(FrozenInstanceError):
        notes.value = "Changed"  # type: ignore[misc]
