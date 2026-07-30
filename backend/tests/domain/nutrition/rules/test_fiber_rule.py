"""Tests for app/domain/nutrition/rules/fiber_rule.py."""

import pytest

from app.domain.nutrition.rules.context import NutritionRuleContext
from app.domain.nutrition.rules.fiber_rule import FiberRule
from app.domain.nutrition.value_objects import Fiber
from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity


@pytest.mark.unit
def test_exposes_id_name_description_severity() -> None:
    rule = FiberRule()
    assert rule.id == RuleId("nutrition.fiber")
    assert rule.name == "Fiber"
    assert rule.description
    assert rule.severity == RecommendationSeverity.WARNING


@pytest.mark.unit
def test_passes_with_no_data() -> None:
    result = FiberRule().evaluate(NutritionRuleContext())
    assert result.passed is True
    assert result.triggered_rules == ()


@pytest.mark.unit
def test_passes_within_the_default_range() -> None:
    result = FiberRule().evaluate(NutritionRuleContext(fiber=Fiber(25.0)))
    assert result.passed is True


@pytest.mark.unit
def test_fails_below_the_minimum() -> None:
    rule = FiberRule()
    result = rule.evaluate(NutritionRuleContext(fiber=Fiber(5.0)))
    assert result.passed is False
    assert result.triggered_rules == (rule.id,)
    assert len(result.recommendations) == 1


@pytest.mark.unit
def test_fails_above_the_maximum() -> None:
    rule = FiberRule()
    result = rule.evaluate(NutritionRuleContext(fiber=Fiber(90.0)))
    assert result.passed is False
    assert len(result.recommendations) == 1


@pytest.mark.unit
def test_thresholds_are_configurable() -> None:
    context = NutritionRuleContext(fiber=Fiber(10.0))
    assert FiberRule(minimum_fiber=5.0).evaluate(context).passed is True
    assert FiberRule(minimum_fiber=20.0).evaluate(context).passed is False


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    context = NutritionRuleContext(fiber=Fiber(5.0))
    rule = FiberRule()
    assert rule.evaluate(context) == rule.evaluate(context)
