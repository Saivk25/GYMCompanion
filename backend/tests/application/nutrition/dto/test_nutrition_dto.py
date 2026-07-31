"""Tests for app/application/nutrition/dto/nutrition_dto.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.application.nutrition.dto.nutrition_dto import NutritionDTO
from app.domain.nutrition.value_objects import Calories, Protein, WaterIntake
from tests.application.nutrition.factories import a_fixed_clock, a_recorded_nutrition


@pytest.mark.unit
def test_from_nutrition_maps_every_field_for_a_freshly_recorded_entry() -> None:
    nutrition = a_recorded_nutrition()

    dto = NutritionDTO.from_nutrition(nutrition)

    assert dto.nutrition_id == nutrition.id
    assert dto.user_id == nutrition.user_id
    assert dto.nutrition_date == nutrition.nutrition_date
    assert dto.recorded_at == nutrition.recorded_at
    assert dto.meal_type is None
    assert dto.source is None
    assert dto.calories is None
    assert dto.protein is None
    assert dto.carbohydrates is None
    assert dto.fat is None
    assert dto.fiber is None
    assert dto.sugar is None
    assert dto.water_intake is None
    assert dto.notes == nutrition.notes
    assert dto.updated_at is None


@pytest.mark.unit
def test_from_nutrition_reflects_updated_macros_and_water() -> None:
    nutrition = a_recorded_nutrition()
    nutrition.update_nutrition(
        calories=Calories(500.0), protein=Protein(30.0), clock=a_fixed_clock()
    )
    nutrition.update_water(WaterIntake(750.0), clock=a_fixed_clock())

    dto = NutritionDTO.from_nutrition(nutrition)

    assert dto.calories == Calories(500.0)
    assert dto.protein == Protein(30.0)
    assert dto.water_intake == WaterIntake(750.0)
    assert dto.updated_at is not None


@pytest.mark.unit
def test_nutrition_dto_is_immutable() -> None:
    dto = NutritionDTO.from_nutrition(a_recorded_nutrition())
    with pytest.raises(FrozenInstanceError):
        dto.calories = Calories(100.0)  # type: ignore[misc]
