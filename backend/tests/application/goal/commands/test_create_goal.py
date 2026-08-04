"""Tests for app/application/goal/commands/create_goal.py."""

from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from app.application.goal.commands.create_goal import CreateGoalCommand
from app.application.shared.command import Command
from app.domain.goal.enums import GoalType
from app.domain.goal.value_objects import GoalName, Priority, TargetDate, TargetWeight
from app.domain.user.identifiers import UserId


def _a_command() -> CreateGoalCommand:
    return CreateGoalCommand(
        user_id=UserId.generate(),
        goal_type=GoalType.LOSE_FAT,
        name=GoalName("Lose 5kg"),
        target_date=TargetDate(date(2026, 6, 1)),
        target_weight=TargetWeight(70.0),
        priority=Priority(1),
    )


@pytest.mark.unit
def test_create_goal_command_is_a_command() -> None:
    assert isinstance(_a_command(), Command)


@pytest.mark.unit
def test_create_goal_command_exposes_its_fields() -> None:
    command = _a_command()
    assert command.goal_type == GoalType.LOSE_FAT
    assert command.name == GoalName("Lose 5kg")
    assert command.target_date == TargetDate(date(2026, 6, 1))
    assert command.target_weight == TargetWeight(70.0)
    assert command.priority == Priority(1)


@pytest.mark.unit
def test_create_goal_command_optional_fields_default_to_none() -> None:
    command = CreateGoalCommand(
        user_id=UserId.generate(),
        goal_type=GoalType.LOSE_FAT,
        name=GoalName("Lose 5kg"),
        target_date=TargetDate(date(2026, 6, 1)),
    )
    assert command.description is None
    assert command.target_weight is None
    assert command.target_body_fat is None
    assert command.target_strength is None
    assert command.priority is None
    assert command.notes is None


@pytest.mark.unit
def test_create_goal_command_is_immutable() -> None:
    command = _a_command()
    with pytest.raises(FrozenInstanceError):
        command.name = GoalName("New Name")  # type: ignore[misc]
