"""Tests for app/application/workout/commands/start_workout_session.py."""

from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from app.application.shared.command import Command
from app.application.workout.commands.start_workout_session import StartWorkoutSessionCommand
from app.domain.workout.identifiers import WorkoutId
from app.domain.workout_session.value_objects import SessionDate


def _a_command() -> StartWorkoutSessionCommand:
    return StartWorkoutSessionCommand(
        workout_id=WorkoutId.generate(), session_date=SessionDate(date(2026, 1, 1))
    )


@pytest.mark.unit
def test_start_workout_session_command_is_a_command() -> None:
    assert isinstance(_a_command(), Command)


@pytest.mark.unit
def test_start_workout_session_command_exposes_its_fields() -> None:
    command = _a_command()
    assert command.session_date == SessionDate(date(2026, 1, 1))


@pytest.mark.unit
def test_start_workout_session_command_carries_no_user_id() -> None:
    """`user_id` is deliberately omitted — derived from the loaded
    Workout's own `user_id` instead."""
    assert not hasattr(_a_command(), "user_id")


@pytest.mark.unit
def test_start_workout_session_command_is_immutable() -> None:
    command = _a_command()
    with pytest.raises(FrozenInstanceError):
        command.session_date = SessionDate(date(2026, 1, 2))  # type: ignore[misc]
