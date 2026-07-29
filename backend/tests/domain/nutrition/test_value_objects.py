"""Tests for app/domain/nutrition/value_objects.py."""

from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from app.domain.nutrition.value_objects import (
    Calories,
    Carbohydrates,
    Fat,
    Fiber,
    MealNotes,
    NutritionDate,
    Protein,
    Sugar,
    WaterIntake,
)
from app.domain.shared_kernel.errors import DomainInvariantViolationError

# --- NutritionDate ---


@pytest.mark.unit
def test_nutrition_date_wraps_a_date() -> None:
    assert NutritionDate(date(2026, 1, 1)).value == date(2026, 1, 1)


@pytest.mark.unit
def test_nutrition_date_is_immutable() -> None:
    nutrition_date = NutritionDate(date(2026, 1, 1))
    with pytest.raises(FrozenInstanceError):
        nutrition_date.value = date(2026, 1, 2)  # type: ignore[misc]


@pytest.mark.unit
def test_nutrition_date_equality_is_by_value() -> None:
    assert NutritionDate(date(2026, 1, 1)) == NutritionDate(date(2026, 1, 1))
    assert NutritionDate(date(2026, 1, 1)) != NutritionDate(date(2026, 1, 2))


# --- Calories / Protein / Carbohydrates / Fat / Fiber / Sugar / WaterIntake:
# all share the same ">= 0" shape (zero explicitly allowed, unlike
# Progress's "> 0" measurements), exercised generically below. ---

_NON_NEGATIVE_TYPES = [Calories, Protein, Carbohydrates, Fat, Fiber, Sugar, WaterIntake]


@pytest.mark.unit
@pytest.mark.parametrize("value_type", _NON_NEGATIVE_TYPES)
@pytest.mark.parametrize("value", [0.0, 0.1, 250.0])
def test_non_negative_types_accept_zero_or_positive_values(value_type: type, value: float) -> None:
    """Zero is explicitly valid — a fasting day, a food with no fat, no
    water logged yet — unlike Progress's strictly-positive measurements."""
    assert value_type(value).value == value


@pytest.mark.unit
@pytest.mark.parametrize("value_type", _NON_NEGATIVE_TYPES)
def test_non_negative_types_reject_a_negative_value(value_type: type) -> None:
    with pytest.raises(DomainInvariantViolationError, match="must not be negative"):
        value_type(-0.1)


@pytest.mark.unit
@pytest.mark.parametrize("value_type", _NON_NEGATIVE_TYPES)
def test_non_negative_types_are_immutable(value_type: type) -> None:
    instance = value_type(10.0)
    with pytest.raises(FrozenInstanceError):
        instance.value = 20.0


@pytest.mark.unit
def test_non_negative_types_are_all_distinct() -> None:
    """Primitive-obsession guard: a `Fat` must not be accidentally
    interchangeable with a `Protein` even though both wrap "a non-negative
    float"."""
    assert len(set(_NON_NEGATIVE_TYPES)) == len(_NON_NEGATIVE_TYPES)
    assert Fat(10.0) != Protein(10.0)  # type: ignore[comparison-overlap]


# --- MealNotes ---


@pytest.mark.unit
def test_meal_notes_defaults_to_empty() -> None:
    assert MealNotes().value == ""


@pytest.mark.unit
def test_meal_notes_accepts_an_explicitly_empty_value() -> None:
    assert MealNotes("").value == ""


@pytest.mark.unit
def test_meal_notes_accepts_a_non_empty_value() -> None:
    assert MealNotes("Post-workout meal.").value == "Post-workout meal."


@pytest.mark.unit
def test_meal_notes_rejects_an_overly_long_value() -> None:
    with pytest.raises(DomainInvariantViolationError, match="at most 2000 characters"):
        MealNotes("x" * 2001)


@pytest.mark.unit
def test_meal_notes_is_immutable() -> None:
    notes = MealNotes("Felt good.")
    with pytest.raises(FrozenInstanceError):
        notes.value = "Changed"  # type: ignore[misc]
