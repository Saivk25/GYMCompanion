"""Tests for app/application/nutrition/commands/record_nutrition.py."""

from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from app.application.nutrition.commands.record_nutrition import RecordNutritionCommand
from app.application.shared.command import Command
from app.domain.nutrition.enums import MealType, NutritionSource
from app.domain.nutrition.value_objects import Calories, NutritionDate, Protein
from app.domain.user.identifiers import UserId


def _a_command() -> RecordNutritionCommand:
    return RecordNutritionCommand(
        user_id=UserId.generate(),
        nutrition_date=NutritionDate(date(2026, 1, 1)),
        meal_type=MealType.BREAKFAST,
        source=NutritionSource.MANUAL,
        calories=Calories(500.0),
        protein=Protein(30.0),
    )


@pytest.mark.unit
def test_record_nutrition_command_is_a_command() -> None:
    assert isinstance(_a_command(), Command)


@pytest.mark.unit
def test_record_nutrition_command_exposes_its_fields() -> None:
    command = _a_command()
    assert command.nutrition_date == NutritionDate(date(2026, 1, 1))
    assert command.meal_type == MealType.BREAKFAST
    assert command.source == NutritionSource.MANUAL
    assert command.calories == Calories(500.0)
    assert command.protein == Protein(30.0)


@pytest.mark.unit
def test_record_nutrition_command_optional_fields_default_to_none() -> None:
    command = RecordNutritionCommand(
        user_id=UserId.generate(), nutrition_date=NutritionDate(date(2026, 1, 1))
    )
    assert command.meal_type is None
    assert command.source is None
    assert command.calories is None
    assert command.protein is None
    assert command.carbohydrates is None
    assert command.fat is None
    assert command.fiber is None
    assert command.sugar is None
    assert command.water_intake is None
    assert command.notes is None


@pytest.mark.unit
def test_record_nutrition_command_is_immutable() -> None:
    command = _a_command()
    with pytest.raises(FrozenInstanceError):
        command.calories = Calories(600.0)  # type: ignore[misc]
