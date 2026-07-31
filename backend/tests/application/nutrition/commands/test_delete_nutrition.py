"""Tests for app/application/nutrition/commands/delete_nutrition.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.application.nutrition.commands.delete_nutrition import DeleteNutritionCommand
from app.application.shared.command import Command
from app.domain.nutrition.identifiers import NutritionId


def _a_command() -> DeleteNutritionCommand:
    return DeleteNutritionCommand(nutrition_id=NutritionId.generate())


@pytest.mark.unit
def test_delete_nutrition_command_is_a_command() -> None:
    assert isinstance(_a_command(), Command)


@pytest.mark.unit
def test_delete_nutrition_command_exposes_its_nutrition_id() -> None:
    nutrition_id = NutritionId.generate()
    command = DeleteNutritionCommand(nutrition_id=nutrition_id)
    assert command.nutrition_id == nutrition_id


@pytest.mark.unit
def test_delete_nutrition_command_is_immutable() -> None:
    command = _a_command()
    with pytest.raises(FrozenInstanceError):
        command.nutrition_id = NutritionId.generate()  # type: ignore[misc]
