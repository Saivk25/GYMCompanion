"""Tests for app/application/user/commands/update_equipment.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.application.shared.command import Command
from app.application.user.commands.update_equipment import UpdateEquipmentCommand
from app.domain.exercise.value_objects import EquipmentRequirement
from app.domain.user.identifiers import UserId


def _a_command() -> UpdateEquipmentCommand:
    return UpdateEquipmentCommand(
        user_id=UserId.generate(), available_equipment=frozenset({EquipmentRequirement("barbell")})
    )


@pytest.mark.unit
def test_update_equipment_command_is_a_command() -> None:
    assert isinstance(_a_command(), Command)


@pytest.mark.unit
def test_update_equipment_command_exposes_its_fields() -> None:
    user_id = UserId.generate()
    equipment = frozenset({EquipmentRequirement("barbell"), EquipmentRequirement("bench")})
    command = UpdateEquipmentCommand(user_id=user_id, available_equipment=equipment)
    assert command.user_id == user_id
    assert command.available_equipment == equipment


@pytest.mark.unit
def test_update_equipment_command_accepts_an_empty_set() -> None:
    command = UpdateEquipmentCommand(user_id=UserId.generate(), available_equipment=frozenset())
    assert command.available_equipment == frozenset()


@pytest.mark.unit
def test_update_equipment_command_is_immutable() -> None:
    command = _a_command()
    with pytest.raises(FrozenInstanceError):
        command.user_id = UserId.generate()  # type: ignore[misc]
