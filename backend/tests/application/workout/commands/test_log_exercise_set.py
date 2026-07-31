"""Tests for app/application/workout/commands/log_exercise_set.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.application.shared.command import Command
from app.application.workout.commands.log_exercise_set import LogExerciseSetCommand
from app.domain.exercise.identifiers import ExerciseId
from app.domain.workout_session.exercise_set import SetNumber, SetReps, SetRPE, SetWeight
from app.domain.workout_session.identifiers import WorkoutSessionId


def _a_command() -> LogExerciseSetCommand:
    return LogExerciseSetCommand(
        session_id=WorkoutSessionId.generate(),
        exercise_id=ExerciseId.generate(),
        set_number=SetNumber(1),
        weight=SetWeight(100.0),
        reps=SetReps(5),
        rpe=SetRPE(7),
    )


@pytest.mark.unit
def test_log_exercise_set_command_is_a_command() -> None:
    assert isinstance(_a_command(), Command)


@pytest.mark.unit
def test_log_exercise_set_command_exposes_its_fields() -> None:
    command = _a_command()
    assert command.set_number == SetNumber(1)
    assert command.weight == SetWeight(100.0)
    assert command.reps == SetReps(5)
    assert command.rpe == SetRPE(7)


@pytest.mark.unit
def test_log_exercise_set_command_carries_no_performance_id() -> None:
    """No `performance_id` field: the handler finds-or-creates the
    matching `ExercisePerformance` itself."""
    assert not hasattr(_a_command(), "performance_id")


@pytest.mark.unit
def test_log_exercise_set_command_is_immutable() -> None:
    command = _a_command()
    with pytest.raises(FrozenInstanceError):
        command.reps = SetReps(10)  # type: ignore[misc]
