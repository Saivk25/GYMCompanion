"""Tests for app/domain/nutrition/context.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.domain.nutrition.context import NutritionContext
from app.domain.nutrition.value_objects import Calories, MealNotes, WaterIntake
from tests.domain.nutrition.factories import a_fixed_clock, a_recorded_nutrition


@pytest.mark.unit
def test_from_nutrition_snapshots_every_relevant_field() -> None:
    nutrition = a_recorded_nutrition()

    context = NutritionContext.from_nutrition(nutrition)

    assert context.nutrition_id == nutrition.id
    assert context.user_id == nutrition.user_id
    assert context.nutrition_date == nutrition.nutrition_date
    assert context.meal_type is None
    assert context.source is None
    assert context.calories is None
    assert context.protein is None
    assert context.carbohydrates is None
    assert context.fat is None
    assert context.fiber is None
    assert context.sugar is None
    assert context.water_intake is None
    assert context.notes == MealNotes()


@pytest.mark.unit
def test_is_immutable() -> None:
    nutrition = a_recorded_nutrition()
    context = NutritionContext.from_nutrition(nutrition)
    with pytest.raises(FrozenInstanceError):
        context.notes = MealNotes("changed")  # type: ignore[misc]


@pytest.mark.unit
def test_does_not_reflect_later_mutations_of_the_source_nutrition() -> None:
    nutrition = a_recorded_nutrition()
    context = NutritionContext.from_nutrition(nutrition)

    nutrition.update_nutrition(calories=Calories(500.0), clock=a_fixed_clock())
    nutrition.update_water(WaterIntake(500.0), clock=a_fixed_clock())

    assert context.calories is None
    assert context.water_intake is None
    assert nutrition.calories == Calories(500.0)
    assert nutrition.water_intake == WaterIntake(500.0)
