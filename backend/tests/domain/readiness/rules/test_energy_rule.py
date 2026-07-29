"""Tests for app/domain/readiness/rules/energy_rule.py."""

import pytest

from app.domain.readiness.rules.context import ReadinessRuleContext
from app.domain.readiness.rules.energy_rule import EnergyRule
from app.domain.readiness.value_objects import EnergyLevel
from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity


@pytest.mark.unit
def test_exposes_id_name_description_severity() -> None:
    rule = EnergyRule()
    assert rule.id == RuleId("readiness.energy_level")
    assert rule.name == "Energy Level"
    assert rule.description
    assert rule.severity == RecommendationSeverity.WARNING


@pytest.mark.unit
def test_passes_with_no_data() -> None:
    result = EnergyRule().evaluate(ReadinessRuleContext())
    assert result.passed is True
    assert result.triggered_rules == ()


@pytest.mark.unit
def test_passes_when_energy_meets_the_minimum() -> None:
    result = EnergyRule().evaluate(ReadinessRuleContext(energy_level=EnergyLevel(4)))
    assert result.passed is True


@pytest.mark.unit
def test_fails_when_energy_is_below_the_minimum() -> None:
    rule = EnergyRule()
    result = rule.evaluate(ReadinessRuleContext(energy_level=EnergyLevel(3)))
    assert result.passed is False
    assert result.triggered_rules == (rule.id,)


@pytest.mark.unit
def test_failure_carries_a_recommendation() -> None:
    result = EnergyRule().evaluate(ReadinessRuleContext(energy_level=EnergyLevel(1)))
    assert len(result.recommendations) == 1


@pytest.mark.unit
def test_minimum_energy_is_configurable() -> None:
    context = ReadinessRuleContext(energy_level=EnergyLevel(5))
    assert EnergyRule(minimum_energy=3).evaluate(context).passed is True
    assert EnergyRule(minimum_energy=8).evaluate(context).passed is False


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    context = ReadinessRuleContext(energy_level=EnergyLevel(2))
    rule = EnergyRule()
    assert rule.evaluate(context) == rule.evaluate(context)
