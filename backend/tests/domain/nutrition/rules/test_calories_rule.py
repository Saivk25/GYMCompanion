"""Tests for app/domain/nutrition/rules/calories_rule.py."""

import pytest

from app.domain.nutrition.rules.calories_rule import CaloriesRule
from app.domain.nutrition.rules.context import NutritionRuleContext
from app.domain.nutrition.value_objects import Calories
from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity


@pytest.mark.unit
def test_exposes_id_name_description_severity() -> None:
    rule = CaloriesRule()
    assert rule.id == RuleId("nutrition.calories")
    assert rule.name == "Calories"
    assert rule.description
    assert rule.severity == RecommendationSeverity.WARNING


@pytest.mark.unit
def test_passes_with_no_data() -> None:
    result = CaloriesRule().evaluate(NutritionRuleContext())
    assert result.passed is True
    assert result.triggered_rules == ()


@pytest.mark.unit
def test_passes_within_the_default_range() -> None:
    result = CaloriesRule().evaluate(NutritionRuleContext(calories=Calories(2200.0)))
    assert result.passed is True


@pytest.mark.unit
def test_passes_at_exactly_the_minimum_and_maximum() -> None:
    rule = CaloriesRule(minimum_calories=1200.0, maximum_calories=4000.0)
    assert rule.evaluate(NutritionRuleContext(calories=Calories(1200.0))).passed is True
    assert rule.evaluate(NutritionRuleContext(calories=Calories(4000.0))).passed is True


@pytest.mark.unit
def test_fails_below_the_minimum() -> None:
    rule = CaloriesRule()
    result = rule.evaluate(NutritionRuleContext(calories=Calories(800.0)))
    assert result.passed is False
    assert result.triggered_rules == (rule.id,)
    assert len(result.recommendations) == 1
    assert "below the minimum" in result.explanation


@pytest.mark.unit
def test_fails_above_the_maximum() -> None:
    rule = CaloriesRule()
    result = rule.evaluate(NutritionRuleContext(calories=Calories(5000.0)))
    assert result.passed is False
    assert result.triggered_rules == (rule.id,)
    assert len(result.recommendations) == 1
    assert "above the maximum" in result.explanation


@pytest.mark.unit
def test_thresholds_are_configurable() -> None:
    context = NutritionRuleContext(calories=Calories(1000.0))
    assert CaloriesRule(minimum_calories=500.0).evaluate(context).passed is True
    assert CaloriesRule(minimum_calories=1500.0).evaluate(context).passed is False


@pytest.mark.unit
def test_severity_is_configurable() -> None:
    rule = CaloriesRule(severity=RecommendationSeverity.CRITICAL)
    result = rule.evaluate(NutritionRuleContext(calories=Calories(100.0)))
    assert result.severity == RecommendationSeverity.CRITICAL


@pytest.mark.unit
def test_rule_id_is_configurable() -> None:
    rule = CaloriesRule(rule_id=RuleId("custom.calories"))
    assert rule.id == RuleId("custom.calories")


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    context = NutritionRuleContext(calories=Calories(800.0))
    rule = CaloriesRule()
    assert rule.evaluate(context) == rule.evaluate(context)
