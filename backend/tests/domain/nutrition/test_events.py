"""Tests for app/domain/nutrition/events.py.

Immutability, `event_id` auto-generation, and `occurred_at` timezone
enforcement are `DomainEvent` base behavior, already fully covered by
`tests/domain/shared_kernel/test_events.py`. This file only proves each
Nutrition-specific event carries the fields it's supposed to.
"""

from datetime import date, datetime, timezone

import pytest

from app.domain.nutrition.enums import MealType, NutritionSource
from app.domain.nutrition.events import (
    MealNotesUpdated,
    NutritionRecorded,
    NutritionUpdated,
    WaterUpdated,
)
from app.domain.nutrition.identifiers import NutritionId
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
from app.domain.user.identifiers import UserId


@pytest.mark.unit
def test_nutrition_recorded_carries_identifying_fields() -> None:
    nutrition_id = NutritionId.generate()
    user_id = UserId.generate()
    nutrition_date = NutritionDate(date(2026, 1, 1))
    event = NutritionRecorded(
        occurred_at=datetime.now(timezone.utc),
        nutrition_id=nutrition_id,
        user_id=user_id,
        nutrition_date=nutrition_date,
        meal_type=MealType.BREAKFAST,
        source=NutritionSource.MANUAL,
    )
    assert event.nutrition_id == nutrition_id
    assert event.user_id == user_id
    assert event.nutrition_date == nutrition_date
    assert event.meal_type == MealType.BREAKFAST
    assert event.source == NutritionSource.MANUAL


@pytest.mark.unit
def test_nutrition_recorded_allows_meal_type_and_source_to_be_none() -> None:
    event = NutritionRecorded(
        occurred_at=datetime.now(timezone.utc),
        nutrition_id=NutritionId.generate(),
        user_id=UserId.generate(),
        nutrition_date=NutritionDate(date(2026, 1, 1)),
        meal_type=None,
        source=None,
    )
    assert event.meal_type is None
    assert event.source is None


@pytest.mark.unit
def test_nutrition_updated_carries_all_six_fields() -> None:
    nutrition_id = NutritionId.generate()
    calories = Calories(500.0)
    protein = Protein(30.0)
    carbohydrates = Carbohydrates(50.0)
    fat = Fat(15.0)
    fiber = Fiber(8.0)
    sugar = Sugar(5.0)
    event = NutritionUpdated(
        occurred_at=datetime.now(timezone.utc),
        nutrition_id=nutrition_id,
        user_id=UserId.generate(),
        calories=calories,
        protein=protein,
        carbohydrates=carbohydrates,
        fat=fat,
        fiber=fiber,
        sugar=sugar,
    )
    assert event.nutrition_id == nutrition_id
    assert event.calories == calories
    assert event.protein == protein
    assert event.carbohydrates == carbohydrates
    assert event.fat == fat
    assert event.fiber == fiber
    assert event.sugar == sugar


@pytest.mark.unit
def test_nutrition_updated_allows_any_field_to_be_none() -> None:
    event = NutritionUpdated(
        occurred_at=datetime.now(timezone.utc),
        nutrition_id=NutritionId.generate(),
        user_id=UserId.generate(),
        calories=None,
        protein=None,
        carbohydrates=None,
        fat=None,
        fiber=None,
        sugar=None,
    )
    assert event.calories is None
    assert event.sugar is None


@pytest.mark.unit
def test_water_updated_carries_the_water_intake() -> None:
    nutrition_id = NutritionId.generate()
    water_intake = WaterIntake(500.0)
    event = WaterUpdated(
        occurred_at=datetime.now(timezone.utc),
        nutrition_id=nutrition_id,
        user_id=UserId.generate(),
        water_intake=water_intake,
    )
    assert event.nutrition_id == nutrition_id
    assert event.water_intake == water_intake


@pytest.mark.unit
def test_meal_notes_updated_carries_the_full_new_notes() -> None:
    nutrition_id = NutritionId.generate()
    notes = MealNotes("Post-workout meal.")
    event = MealNotesUpdated(
        occurred_at=datetime.now(timezone.utc),
        nutrition_id=nutrition_id,
        user_id=UserId.generate(),
        notes=notes,
    )
    assert event.nutrition_id == nutrition_id
    assert event.notes == notes
