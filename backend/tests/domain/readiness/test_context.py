"""Tests for app/domain/readiness/context.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.domain.readiness.context import ReadinessContext
from app.domain.readiness.value_objects import EnergyLevel, RecoveryNotes, SleepQuality
from tests.domain.readiness.factories import a_fixed_clock, a_recorded_readiness


@pytest.mark.unit
def test_from_readiness_snapshots_every_relevant_field() -> None:
    readiness = a_recorded_readiness()

    context = ReadinessContext.from_readiness(readiness)

    assert context.readiness_id == readiness.id
    assert context.user_id == readiness.user_id
    assert context.readiness_date == readiness.readiness_date
    assert context.source is None
    assert context.sleep_duration is None
    assert context.sleep_quality is None
    assert context.energy_level is None
    assert context.stress_level is None
    assert context.soreness_level is None
    assert context.resting_heart_rate is None
    assert context.heart_rate_variability is None
    assert context.notes == RecoveryNotes()


@pytest.mark.unit
def test_is_immutable() -> None:
    readiness = a_recorded_readiness()
    context = ReadinessContext.from_readiness(readiness)
    with pytest.raises(FrozenInstanceError):
        context.notes = RecoveryNotes("changed")  # type: ignore[misc]


@pytest.mark.unit
def test_does_not_reflect_later_mutations_of_the_source_readiness() -> None:
    readiness = a_recorded_readiness()
    context = ReadinessContext.from_readiness(readiness)

    readiness.update_sleep(sleep_quality=SleepQuality(8), clock=a_fixed_clock())
    readiness.update_recovery_metrics(energy_level=EnergyLevel(7), clock=a_fixed_clock())

    assert context.sleep_quality is None
    assert context.energy_level is None
    assert readiness.sleep_quality == SleepQuality(8)
    assert readiness.energy_level == EnergyLevel(7)
