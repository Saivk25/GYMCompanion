"""Tests for app/application/nutrition/commands/update_nutrition.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.application.nutrition.commands.update_nutrition import UpdateNutritionCommand
from app.application.shared.command import Command
from app.domain.nutrition.identifiers import NutritionId
from app.domain.nutrition.value_objects import Calories, Carbohydrates, Fat, Fiber, Protein, Sugar


def _a_command() -> UpdateNutritionCommand:
    return UpdateNutritionCommand(
        nutrition_id=NutritionId.generate(),
        calories=Calories(600.0),
        protein=Protein(40.0),
        carbohydrates=Carbohydrates(50.0),
        fat=Fat(20.0),
        fiber=Fiber(8.0),
        sugar=Sugar(10.0),
    )


@pytest.mark.unit
def test_update_nutrition_command_is_a_command() -> None:
    assert isinstance(_a_command(), Command)


@pytest.mark.unit
def test_update_nutrition_command_exposes_its_fields() -> None:
    command = _a_command()
    assert command.calories == Calories(600.0)
    assert command.protein == Protein(40.0)
    assert command.carbohydrates == Carbohydrates(50.0)
    assert command.fat == Fat(20.0)
    assert command.fiber == Fiber(8.0)
    assert command.sugar == Sugar(10.0)


@pytest.mark.unit
def test_update_nutrition_command_fields_default_to_none_meaning_unchanged() -> None:
    command = UpdateNutritionCommand(nutrition_id=NutritionId.generate())
    assert command.calories is None
    assert command.protein is None
    assert command.carbohydrates is None
    assert command.fat is None
    assert command.fiber is None
    assert command.sugar is None


@pytest.mark.unit
def test_update_nutrition_command_is_immutable() -> None:
    command = _a_command()
    with pytest.raises(FrozenInstanceError):
        command.calories = None  # type: ignore[misc]
