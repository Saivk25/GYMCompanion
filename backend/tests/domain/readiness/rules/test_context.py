"""Tests for app/domain/readiness/rules/context.py."""

from dataclasses import FrozenInstanceError
from datetime import timedelta

import pytest

from app.domain.readiness.rules.context import ReadinessRuleContext
from app.domain.readiness.value_objects import EnergyLevel, SleepDuration
from app.domain.rules.context import RuleContext
from tests.domain.readiness.factories import a_fixed_clock, a_recorded_readiness


@pytest.mark.unit
def test_is_a_rule_context() -> None:
    assert isinstance(ReadinessRuleContext(), RuleContext)


@pytest.mark.unit
def test_defaults_every_field_to_none() -> None:
    context = ReadinessRuleContext()
    assert context.sleep_duration is None
    assert context.energy_level is None
    assert context.stress_level is None
    assert context.soreness_level is None
    assert context.resting_heart_rate is None
    assert context.heart_rate_variability is None


@pytest.mark.unit
def test_accepts_every_field_explicitly() -> None:
    context = ReadinessRuleContext(
        sleep_duration=SleepDuration(timedelta(hours=7)),
        energy_level=EnergyLevel(6),
    )
    assert context.sleep_duration == SleepDuration(timedelta(hours=7))
    assert context.energy_level == EnergyLevel(6)


@pytest.mark.unit
def test_is_immutable() -> None:
    context = ReadinessRuleContext()
    with pytest.raises(FrozenInstanceError):
        context.energy_level = EnergyLevel(5)  # type: ignore[misc]


# --- from_readiness() ---


@pytest.mark.unit
def test_from_readiness_maps_only_the_six_rule_relevant_fields() -> None:
    readiness = a_recorded_readiness()
    readiness.update_sleep(sleep_duration=SleepDuration(timedelta(hours=6)), clock=a_fixed_clock())
    readiness.update_recovery_metrics(energy_level=EnergyLevel(5), clock=a_fixed_clock())

    context = ReadinessRuleContext.from_readiness(readiness)

    assert context.sleep_duration == readiness.sleep_duration
    assert context.energy_level == readiness.energy_level
    assert context.stress_level == readiness.stress_level
    assert context.soreness_level == readiness.soreness_level
    assert context.resting_heart_rate == readiness.resting_heart_rate
    assert context.heart_rate_variability == readiness.heart_rate_variability


@pytest.mark.unit
def test_from_readiness_with_no_optional_fields_recorded() -> None:
    readiness = a_recorded_readiness()
    context = ReadinessRuleContext.from_readiness(readiness)
    assert context.sleep_duration is None
    assert context.energy_level is None
    assert context.stress_level is None
    assert context.soreness_level is None
    assert context.resting_heart_rate is None
    assert context.heart_rate_variability is None


@pytest.mark.unit
def test_from_readiness_does_not_reflect_later_mutations() -> None:
    readiness = a_recorded_readiness()
    context = ReadinessRuleContext.from_readiness(readiness)

    readiness.update_recovery_metrics(energy_level=EnergyLevel(8), clock=a_fixed_clock())

    assert context.energy_level is None
    assert readiness.energy_level == EnergyLevel(8)
