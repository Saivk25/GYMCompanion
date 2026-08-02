"""Tests for app/application/progress/commands/update_body_composition.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.application.progress.commands.update_body_composition import (
    UpdateBodyCompositionCommand,
)
from app.application.shared.command import Command
from app.domain.progress.identifiers import ProgressId
from app.domain.progress.value_objects import BodyFatPercentage, BodyWeight


def _a_command() -> UpdateBodyCompositionCommand:
    return UpdateBodyCompositionCommand(
        progress_id=ProgressId.generate(),
        body_weight=BodyWeight(80.0),
        body_fat_percentage=BodyFatPercentage(20.0),
    )


@pytest.mark.unit
def test_update_body_composition_command_is_a_command() -> None:
    assert isinstance(_a_command(), Command)


@pytest.mark.unit
def test_update_body_composition_command_exposes_its_fields() -> None:
    command = _a_command()
    assert command.body_weight == BodyWeight(80.0)
    assert command.body_fat_percentage == BodyFatPercentage(20.0)


@pytest.mark.unit
def test_update_body_composition_command_fields_default_to_none_meaning_unchanged() -> None:
    command = UpdateBodyCompositionCommand(progress_id=ProgressId.generate())
    assert command.body_weight is None
    assert command.body_fat_percentage is None
    assert command.lean_body_mass is None
    assert command.muscle_mass is None


@pytest.mark.unit
def test_update_body_composition_command_is_immutable() -> None:
    command = _a_command()
    with pytest.raises(FrozenInstanceError):
        command.body_weight = BodyWeight(90.0)  # type: ignore[misc]
