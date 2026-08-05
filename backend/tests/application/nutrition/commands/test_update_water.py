"""Tests for app/application/nutrition/commands/update_water.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.application.nutrition.commands.update_water import UpdateWaterCommand
from app.application.shared.command import Command
from app.domain.nutrition.identifiers import NutritionId
from app.domain.nutrition.value_objects import WaterIntake
from app.domain.user.identifiers import UserId


def _a_command() -> UpdateWaterCommand:
    return UpdateWaterCommand(
        nutrition_id=NutritionId.generate(),
        requester_id=UserId.generate(),
        water_intake=WaterIntake(500.0),
    )


@pytest.mark.unit
def test_update_water_command_is_a_command() -> None:
    assert isinstance(_a_command(), Command)


@pytest.mark.unit
def test_update_water_command_exposes_its_fields() -> None:
    command = _a_command()
    assert command.water_intake == WaterIntake(500.0)


@pytest.mark.unit
def test_update_water_command_is_immutable() -> None:
    command = _a_command()
    with pytest.raises(FrozenInstanceError):
        command.water_intake = WaterIntake(600.0)  # type: ignore[misc]
