"""Tests for app/application/workout/commands/update_workout.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.application.shared.command import Command
from app.application.workout.commands.update_workout import UpdateWorkoutCommand
from app.domain.workout.identifiers import WorkoutId
from app.domain.workout.value_objects import WorkoutGoal, WorkoutNotes


def _a_command() -> UpdateWorkoutCommand:
    return UpdateWorkoutCommand(
        workout_id=WorkoutId.generate(),
        goal=WorkoutGoal("hypertrophy"),
        notes=WorkoutNotes("new plan"),
    )


@pytest.mark.unit
def test_update_workout_command_is_a_command() -> None:
    assert isinstance(_a_command(), Command)


@pytest.mark.unit
def test_update_workout_command_exposes_its_fields() -> None:
    command = _a_command()
    assert command.goal == WorkoutGoal("hypertrophy")
    assert command.notes == WorkoutNotes("new plan")


@pytest.mark.unit
def test_update_workout_command_accepts_none_for_both_fields() -> None:
    """`None` means "clear," not "leave unchanged" — both fields are
    required, full-replace semantics."""
    command = UpdateWorkoutCommand(workout_id=WorkoutId.generate(), goal=None, notes=None)
    assert command.goal is None
    assert command.notes is None


@pytest.mark.unit
def test_update_workout_command_is_immutable() -> None:
    command = _a_command()
    with pytest.raises(FrozenInstanceError):
        command.goal = None  # type: ignore[misc]
