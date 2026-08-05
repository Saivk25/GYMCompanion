"""Tests for app/application/goal/commands/complete_goal.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.application.goal.commands.complete_goal import CompleteGoalCommand
from app.application.shared.command import Command
from app.domain.goal.identifiers import GoalId
from app.domain.user.identifiers import UserId


@pytest.mark.unit
def test_complete_goal_command_is_a_command() -> None:
    assert isinstance(
        CompleteGoalCommand(goal_id=GoalId.generate(), requester_id=UserId.generate()), Command
    )


@pytest.mark.unit
def test_complete_goal_command_exposes_its_goal_id() -> None:
    goal_id = GoalId.generate()
    command = CompleteGoalCommand(goal_id=goal_id, requester_id=UserId.generate())
    assert command.goal_id == goal_id


@pytest.mark.unit
def test_complete_goal_command_is_immutable() -> None:
    command = CompleteGoalCommand(goal_id=GoalId.generate(), requester_id=UserId.generate())
    with pytest.raises(FrozenInstanceError):
        command.goal_id = GoalId.generate()  # type: ignore[misc]
