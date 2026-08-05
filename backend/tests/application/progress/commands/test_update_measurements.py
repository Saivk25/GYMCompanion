"""Tests for app/application/progress/commands/update_measurements.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.application.progress.commands.update_measurements import UpdateMeasurementsCommand
from app.application.shared.command import Command
from app.domain.progress.identifiers import ProgressId
from app.domain.progress.value_objects import ChestMeasurement, WaistMeasurement
from app.domain.user.identifiers import UserId


def _a_command() -> UpdateMeasurementsCommand:
    return UpdateMeasurementsCommand(
        progress_id=ProgressId.generate(),
        requester_id=UserId.generate(),
        waist=WaistMeasurement(85.0),
        chest=ChestMeasurement(100.0),
    )


@pytest.mark.unit
def test_update_measurements_command_is_a_command() -> None:
    assert isinstance(_a_command(), Command)


@pytest.mark.unit
def test_update_measurements_command_exposes_its_fields() -> None:
    command = _a_command()
    assert command.waist == WaistMeasurement(85.0)
    assert command.chest == ChestMeasurement(100.0)


@pytest.mark.unit
def test_update_measurements_command_fields_default_to_none_meaning_unchanged() -> None:
    command = UpdateMeasurementsCommand(
        progress_id=ProgressId.generate(), requester_id=UserId.generate()
    )
    assert command.waist is None
    assert command.chest is None
    assert command.hip is None
    assert command.arm is None
    assert command.thigh is None
    assert command.calf is None
    assert command.neck is None


@pytest.mark.unit
def test_update_measurements_command_is_immutable() -> None:
    command = _a_command()
    with pytest.raises(FrozenInstanceError):
        command.waist = WaistMeasurement(90.0)  # type: ignore[misc]
