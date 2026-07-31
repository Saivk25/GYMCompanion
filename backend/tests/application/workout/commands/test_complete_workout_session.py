"""Tests for app/application/workout/commands/complete_workout_session.py."""

from dataclasses import FrozenInstanceError
from datetime import timedelta

import pytest

from app.application.shared.command import Command
from app.application.workout.commands.complete_workout_session import (
    CompleteWorkoutSessionCommand,
)
from app.domain.workout_session.identifiers import WorkoutSessionId
from app.domain.workout_session.value_objects import (
    CompletionPercentage,
    SessionDuration,
    SessionRating,
)


def _a_command() -> CompleteWorkoutSessionCommand:
    return CompleteWorkoutSessionCommand(
        session_id=WorkoutSessionId.generate(),
        duration=SessionDuration(timedelta(minutes=45)),
        completion_percentage=CompletionPercentage(100.0),
        rating=SessionRating(8),
    )


@pytest.mark.unit
def test_complete_workout_session_command_is_a_command() -> None:
    assert isinstance(_a_command(), Command)


@pytest.mark.unit
def test_complete_workout_session_command_exposes_its_fields() -> None:
    command = _a_command()
    assert command.duration == SessionDuration(timedelta(minutes=45))
    assert command.completion_percentage == CompletionPercentage(100.0)
    assert command.rating == SessionRating(8)


@pytest.mark.unit
def test_complete_workout_session_command_rating_defaults_to_none() -> None:
    command = CompleteWorkoutSessionCommand(
        session_id=WorkoutSessionId.generate(),
        duration=SessionDuration(timedelta(minutes=45)),
        completion_percentage=CompletionPercentage(100.0),
    )
    assert command.rating is None


@pytest.mark.unit
def test_complete_workout_session_command_is_immutable() -> None:
    command = _a_command()
    with pytest.raises(FrozenInstanceError):
        command.rating = None  # type: ignore[misc]
