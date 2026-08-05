"""Tests for app/application/workout/commands/complete_exercise_set.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.application.shared.command import Command
from app.application.workout.commands.complete_exercise_set import CompleteExerciseSetCommand
from app.domain.user.identifiers import UserId
from app.domain.workout_session.identifiers import ExercisePerformanceId, WorkoutSessionId


def _a_command() -> CompleteExerciseSetCommand:
    return CompleteExerciseSetCommand(
        session_id=WorkoutSessionId.generate(),
        requester_id=UserId.generate(),
        performance_id=ExercisePerformanceId.generate(),
        set_number=1,
    )


@pytest.mark.unit
def test_complete_exercise_set_command_is_a_command() -> None:
    assert isinstance(_a_command(), Command)


@pytest.mark.unit
def test_complete_exercise_set_command_exposes_its_fields() -> None:
    command = _a_command()
    assert command.set_number == 1
    assert isinstance(command.set_number, int)


@pytest.mark.unit
def test_complete_exercise_set_command_exposes_its_requester_id() -> None:
    requester_id = UserId.generate()
    command = CompleteExerciseSetCommand(
        session_id=WorkoutSessionId.generate(),
        requester_id=requester_id,
        performance_id=ExercisePerformanceId.generate(),
        set_number=1,
    )
    assert command.requester_id == requester_id


@pytest.mark.unit
def test_complete_exercise_set_command_is_immutable() -> None:
    command = _a_command()
    with pytest.raises(FrozenInstanceError):
        command.set_number = 2  # type: ignore[misc]
