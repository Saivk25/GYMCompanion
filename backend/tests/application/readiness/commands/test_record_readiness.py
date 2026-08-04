"""Tests for app/application/readiness/commands/record_readiness.py."""

from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from app.application.readiness.commands.record_readiness import RecordReadinessCommand
from app.application.shared.command import Command
from app.domain.readiness.enums import ReadinessSource
from app.domain.readiness.value_objects import EnergyLevel, ReadinessDate, SleepQuality
from app.domain.user.identifiers import UserId


def _a_command() -> RecordReadinessCommand:
    return RecordReadinessCommand(
        user_id=UserId.generate(),
        readiness_date=ReadinessDate(date(2026, 1, 1)),
        source=ReadinessSource.MANUAL,
        sleep_quality=SleepQuality(7),
        energy_level=EnergyLevel(6),
    )


@pytest.mark.unit
def test_record_readiness_command_is_a_command() -> None:
    assert isinstance(_a_command(), Command)


@pytest.mark.unit
def test_record_readiness_command_exposes_its_fields() -> None:
    command = _a_command()
    assert command.readiness_date == ReadinessDate(date(2026, 1, 1))
    assert command.source == ReadinessSource.MANUAL
    assert command.sleep_quality == SleepQuality(7)
    assert command.energy_level == EnergyLevel(6)


@pytest.mark.unit
def test_record_readiness_command_optional_fields_default_to_none() -> None:
    command = RecordReadinessCommand(
        user_id=UserId.generate(), readiness_date=ReadinessDate(date(2026, 1, 1))
    )
    assert command.source is None
    assert command.sleep_duration is None
    assert command.sleep_quality is None
    assert command.energy_level is None
    assert command.stress_level is None
    assert command.soreness_level is None
    assert command.resting_heart_rate is None
    assert command.heart_rate_variability is None
    assert command.notes is None


@pytest.mark.unit
def test_record_readiness_command_is_immutable() -> None:
    command = _a_command()
    with pytest.raises(FrozenInstanceError):
        command.energy_level = EnergyLevel(9)  # type: ignore[misc]
