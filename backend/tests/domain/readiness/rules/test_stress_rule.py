"""Tests for app/domain/readiness/rules/stress_rule.py."""

import pytest

from app.domain.readiness.rules.context import ReadinessRuleContext
from app.domain.readiness.rules.stress_rule import StressRule
from app.domain.readiness.value_objects import StressLevel
from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity


@pytest.mark.unit
def test_exposes_id_name_description_severity() -> None:
    rule = StressRule()
    assert rule.id == RuleId("readiness.stress_level")
    assert rule.name == "Stress Level"
    assert rule.description
    assert rule.severity == RecommendationSeverity.WARNING


@pytest.mark.unit
def test_passes_with_no_data() -> None:
    result = StressRule().evaluate(ReadinessRuleContext())
    assert result.passed is True
    assert result.triggered_rules == ()


@pytest.mark.unit
def test_passes_when_stress_is_within_the_maximum() -> None:
    result = StressRule().evaluate(ReadinessRuleContext(stress_level=StressLevel(7)))
    assert result.passed is True


@pytest.mark.unit
def test_fails_when_stress_exceeds_the_maximum() -> None:
    rule = StressRule()
    result = rule.evaluate(ReadinessRuleContext(stress_level=StressLevel(8)))
    assert result.passed is False
    assert result.triggered_rules == (rule.id,)


@pytest.mark.unit
def test_failure_carries_a_recommendation() -> None:
    result = StressRule().evaluate(ReadinessRuleContext(stress_level=StressLevel(10)))
    assert len(result.recommendations) == 1


@pytest.mark.unit
def test_maximum_stress_is_configurable() -> None:
    context = ReadinessRuleContext(stress_level=StressLevel(5))
    assert StressRule(maximum_stress=8).evaluate(context).passed is True
    assert StressRule(maximum_stress=3).evaluate(context).passed is False


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    context = ReadinessRuleContext(stress_level=StressLevel(9))
    rule = StressRule()
    assert rule.evaluate(context) == rule.evaluate(context)
