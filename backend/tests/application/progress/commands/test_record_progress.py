"""Tests for app/application/progress/commands/record_progress.py."""

from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from app.application.progress.commands.record_progress import RecordProgressCommand
from app.application.shared.command import Command
from app.domain.progress.enums import MeasurementUnit, ProgressSource
from app.domain.progress.value_objects import BodyWeight, ProgressDate
from app.domain.user.identifiers import UserId


def _a_command() -> RecordProgressCommand:
    return RecordProgressCommand(
        user_id=UserId.generate(),
        progress_date=ProgressDate(date(2026, 1, 1)),
        unit=MeasurementUnit.METRIC,
        source=ProgressSource.MANUAL,
        body_weight=BodyWeight(80.0),
    )


@pytest.mark.unit
def test_record_progress_command_is_a_command() -> None:
    assert isinstance(_a_command(), Command)


@pytest.mark.unit
def test_record_progress_command_exposes_its_fields() -> None:
    command = _a_command()
    assert command.progress_date == ProgressDate(date(2026, 1, 1))
    assert command.unit == MeasurementUnit.METRIC
    assert command.source == ProgressSource.MANUAL
    assert command.body_weight == BodyWeight(80.0)


@pytest.mark.unit
def test_record_progress_command_optional_fields_default_to_none() -> None:
    command = RecordProgressCommand(
        user_id=UserId.generate(),
        progress_date=ProgressDate(date(2026, 1, 1)),
        unit=MeasurementUnit.METRIC,
        source=ProgressSource.MANUAL,
    )
    assert command.body_weight is None
    assert command.body_fat_percentage is None
    assert command.lean_body_mass is None
    assert command.muscle_mass is None
    assert command.waist is None
    assert command.chest is None
    assert command.hip is None
    assert command.arm is None
    assert command.thigh is None
    assert command.calf is None
    assert command.neck is None
    assert command.notes is None


@pytest.mark.unit
def test_record_progress_command_is_immutable() -> None:
    command = _a_command()
    with pytest.raises(FrozenInstanceError):
        command.body_weight = BodyWeight(90.0)  # type: ignore[misc]
