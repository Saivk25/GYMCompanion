"""Tests for app/application/goal/commands/update_goal.py."""

from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from app.application.goal.commands.update_goal import UpdateGoalCommand
from app.application.shared.command import Command
from app.domain.goal.identifiers import GoalId
from app.domain.goal.value_objects import GoalName, Priority, TargetDate
from app.domain.user.identifiers import UserId


def _a_command() -> UpdateGoalCommand:
    return UpdateGoalCommand(
        goal_id=GoalId.generate(),
        requester_id=UserId.generate(),
        name=GoalName("New Name"),
        target_date=TargetDate(date(2026, 7, 1)),
        priority=Priority(2),
    )


@pytest.mark.unit
def test_update_goal_command_is_a_command() -> None:
    assert isinstance(_a_command(), Command)


@pytest.mark.unit
def test_update_goal_command_exposes_its_fields() -> None:
    command = _a_command()
    assert command.name == GoalName("New Name")
    assert command.target_date == TargetDate(date(2026, 7, 1))
    assert command.priority == Priority(2)


@pytest.mark.unit
def test_update_goal_command_optional_fields_default_to_none() -> None:
    command = UpdateGoalCommand(goal_id=GoalId.generate(), requester_id=UserId.generate())
    assert command.name is None
    assert command.description is None
    assert command.target_date is None
    assert command.target_weight is None
    assert command.target_body_fat is None
    assert command.target_strength is None
    assert command.priority is None
    assert command.notes is None


@pytest.mark.unit
def test_update_goal_command_is_immutable() -> None:
    command = _a_command()
    with pytest.raises(FrozenInstanceError):
        command.name = GoalName("Another Name")  # type: ignore[misc]
