"""Tests for app/application/workout/commands/create_workout.py."""

from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from app.application.shared.command import Command
from app.application.workout.commands.create_workout import CreateWorkoutCommand
from app.domain.user.identifiers import UserId
from app.domain.workout.value_objects import WorkoutDate, WorkoutGoal, WorkoutName, WorkoutNotes


def _a_command() -> CreateWorkoutCommand:
    return CreateWorkoutCommand(
        user_id=UserId.generate(),
        name=WorkoutName("Push Day"),
        planned_date=WorkoutDate(date(2026, 1, 1)),
        goal=WorkoutGoal("upper body strength"),
        notes=WorkoutNotes("felt strong"),
    )


@pytest.mark.unit
def test_create_workout_command_is_a_command() -> None:
    assert isinstance(_a_command(), Command)


@pytest.mark.unit
def test_create_workout_command_exposes_its_fields() -> None:
    command = _a_command()
    assert command.name == WorkoutName("Push Day")
    assert command.planned_date == WorkoutDate(date(2026, 1, 1))
    assert command.goal == WorkoutGoal("upper body strength")
    assert command.notes == WorkoutNotes("felt strong")


@pytest.mark.unit
def test_create_workout_command_goal_and_notes_default_to_none() -> None:
    command = CreateWorkoutCommand(
        user_id=UserId.generate(),
        name=WorkoutName("Push Day"),
        planned_date=WorkoutDate(date(2026, 1, 1)),
    )
    assert command.goal is None
    assert command.notes is None


@pytest.mark.unit
def test_create_workout_command_is_immutable() -> None:
    command = _a_command()
    with pytest.raises(FrozenInstanceError):
        command.name = WorkoutName("Pull Day")  # type: ignore[misc]
