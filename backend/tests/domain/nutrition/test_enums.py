"""Tests for app/domain/nutrition/enums.py."""

import pytest

from app.domain.nutrition.enums import MealType, NutritionSource


@pytest.mark.unit
def test_meal_type_has_exactly_four_members() -> None:
    assert {member.value for member in MealType} == {
        "breakfast",
        "lunch",
        "dinner",
        "snack",
    }


@pytest.mark.unit
def test_meal_type_is_a_str_subclass() -> None:
    assert isinstance(MealType.BREAKFAST, str)
    assert MealType.BREAKFAST.value == "breakfast"


@pytest.mark.unit
def test_nutrition_source_has_exactly_three_members() -> None:
    assert {member.value for member in NutritionSource} == {
        "manual",
        "barcode",
        "import",
    }


@pytest.mark.unit
def test_nutrition_source_is_a_str_subclass() -> None:
    assert isinstance(NutritionSource.MANUAL, str)
    assert NutritionSource.MANUAL.value == "manual"
