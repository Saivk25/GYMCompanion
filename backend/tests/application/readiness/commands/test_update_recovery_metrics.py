"""Tests for
app/application/readiness/commands/update_recovery_metrics.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.application.readiness.commands.update_recovery_metrics import (
    UpdateRecoveryMetricsCommand,
)
from app.application.shared.command import Command
from app.domain.readiness.identifiers import ReadinessId
from app.domain.readiness.value_objects import (
    EnergyLevel,
    HeartRateVariability,
    RestingHeartRate,
    SorenessLevel,
    StressLevel,
)


def _a_command() -> UpdateRecoveryMetricsCommand:
    return UpdateRecoveryMetricsCommand(
        readiness_id=ReadinessId.generate(),
        energy_level=EnergyLevel(6),
        stress_level=StressLevel(4),
        soreness_level=SorenessLevel(3),
        resting_heart_rate=RestingHeartRate(58.0),
        heart_rate_variability=HeartRateVariability(65.0),
    )


@pytest.mark.unit
def test_update_recovery_metrics_command_is_a_command() -> None:
    assert isinstance(_a_command(), Command)


@pytest.mark.unit
def test_update_recovery_metrics_command_exposes_its_fields() -> None:
    command = _a_command()
    assert command.energy_level == EnergyLevel(6)
    assert command.stress_level == StressLevel(4)
    assert command.soreness_level == SorenessLevel(3)
    assert command.resting_heart_rate == RestingHeartRate(58.0)
    assert command.heart_rate_variability == HeartRateVariability(65.0)


@pytest.mark.unit
def test_update_recovery_metrics_command_fields_default_to_none_meaning_unchanged() -> None:
    command = UpdateRecoveryMetricsCommand(readiness_id=ReadinessId.generate())
    assert command.energy_level is None
    assert command.stress_level is None
    assert command.soreness_level is None
    assert command.resting_heart_rate is None
    assert command.heart_rate_variability is None


@pytest.mark.unit
def test_update_recovery_metrics_command_is_immutable() -> None:
    command = _a_command()
    with pytest.raises(FrozenInstanceError):
        command.energy_level = EnergyLevel(9)  # type: ignore[misc]
