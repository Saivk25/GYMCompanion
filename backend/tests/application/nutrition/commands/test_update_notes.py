"""Tests for app/application/nutrition/commands/update_notes.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.application.nutrition.commands.update_notes import UpdateNutritionNotesCommand
from app.application.shared.command import Command
from app.domain.nutrition.identifiers import NutritionId
from app.domain.nutrition.value_objects import MealNotes


def _a_command() -> UpdateNutritionNotesCommand:
    return UpdateNutritionNotesCommand(
        nutrition_id=NutritionId.generate(), notes=MealNotes("post-workout meal")
    )


@pytest.mark.unit
def test_update_nutrition_notes_command_is_a_command() -> None:
    assert isinstance(_a_command(), Command)


@pytest.mark.unit
def test_update_nutrition_notes_command_exposes_its_fields() -> None:
    command = _a_command()
    assert command.notes == MealNotes("post-workout meal")


@pytest.mark.unit
def test_update_nutrition_notes_command_is_immutable() -> None:
    command = _a_command()
    with pytest.raises(FrozenInstanceError):
        command.notes = MealNotes("changed")  # type: ignore[misc]
