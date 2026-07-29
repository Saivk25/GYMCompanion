"""Tests for app/domain/readiness/rules/soreness_rule.py."""

import pytest

from app.domain.readiness.rules.context import ReadinessRuleContext
from app.domain.readiness.rules.soreness_rule import SorenessRule
from app.domain.readiness.value_objects import SorenessLevel
from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity


@pytest.mark.unit
def test_exposes_id_name_description_severity() -> None:
    rule = SorenessRule()
    assert rule.id == RuleId("readiness.soreness_level")
    assert rule.name == "Soreness Level"
    assert rule.description
    assert rule.severity == RecommendationSeverity.WARNING


@pytest.mark.unit
def test_passes_with_no_data() -> None:
    result = SorenessRule().evaluate(ReadinessRuleContext())
    assert result.passed is True
    assert result.triggered_rules == ()


@pytest.mark.unit
def test_passes_when_soreness_is_within_the_maximum() -> None:
    result = SorenessRule().evaluate(ReadinessRuleContext(soreness_level=SorenessLevel(7)))
    assert result.passed is True


@pytest.mark.unit
def test_fails_when_soreness_exceeds_the_maximum() -> None:
    rule = SorenessRule()
    result = rule.evaluate(ReadinessRuleContext(soreness_level=SorenessLevel(8)))
    assert result.passed is False
    assert result.triggered_rules == (rule.id,)


@pytest.mark.unit
def test_failure_carries_a_recommendation() -> None:
    result = SorenessRule().evaluate(ReadinessRuleContext(soreness_level=SorenessLevel(10)))
    assert len(result.recommendations) == 1


@pytest.mark.unit
def test_maximum_soreness_is_configurable() -> None:
    context = ReadinessRuleContext(soreness_level=SorenessLevel(5))
    assert SorenessRule(maximum_soreness=8).evaluate(context).passed is True
    assert SorenessRule(maximum_soreness=3).evaluate(context).passed is False


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    context = ReadinessRuleContext(soreness_level=SorenessLevel(9))
    rule = SorenessRule()
    assert rule.evaluate(context) == rule.evaluate(context)
