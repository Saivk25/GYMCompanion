"""Tests for app/application/workout/commands/cancel_workout.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.application.shared.command import Command
from app.application.workout.commands.cancel_workout import CancelWorkoutCommand
from app.domain.workout.identifiers import WorkoutId


def _a_command() -> CancelWorkoutCommand:
    return CancelWorkoutCommand(workout_id=WorkoutId.generate())


@pytest.mark.unit
def test_cancel_workout_command_is_a_command() -> None:
    assert isinstance(_a_command(), Command)


@pytest.mark.unit
def test_cancel_workout_command_exposes_its_workout_id() -> None:
    workout_id = WorkoutId.generate()
    command = CancelWorkoutCommand(workout_id=workout_id)
    assert command.workout_id == workout_id


@pytest.mark.unit
def test_cancel_workout_command_is_immutable() -> None:
    command = _a_command()
    with pytest.raises(FrozenInstanceError):
        command.workout_id = WorkoutId.generate()  # type: ignore[misc]
