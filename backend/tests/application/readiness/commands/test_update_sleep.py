"""Tests for app/application/readiness/commands/update_sleep.py."""

from dataclasses import FrozenInstanceError
from datetime import timedelta

import pytest

from app.application.readiness.commands.update_sleep import UpdateSleepCommand
from app.application.shared.command import Command
from app.domain.readiness.identifiers import ReadinessId
from app.domain.readiness.value_objects import SleepDuration, SleepQuality


def _a_command() -> UpdateSleepCommand:
    return UpdateSleepCommand(
        readiness_id=ReadinessId.generate(),
        sleep_duration=SleepDuration(timedelta(hours=7)),
        sleep_quality=SleepQuality(8),
    )


@pytest.mark.unit
def test_update_sleep_command_is_a_command() -> None:
    assert isinstance(_a_command(), Command)


@pytest.mark.unit
def test_update_sleep_command_exposes_its_fields() -> None:
    command = _a_command()
    assert command.sleep_duration == SleepDuration(timedelta(hours=7))
    assert command.sleep_quality == SleepQuality(8)


@pytest.mark.unit
def test_update_sleep_command_fields_default_to_none_meaning_unchanged() -> None:
    command = UpdateSleepCommand(readiness_id=ReadinessId.generate())
    assert command.sleep_duration is None
    assert command.sleep_quality is None


@pytest.mark.unit
def test_update_sleep_command_is_immutable() -> None:
    command = _a_command()
    with pytest.raises(FrozenInstanceError):
        command.sleep_quality = SleepQuality(5)  # type: ignore[misc]
