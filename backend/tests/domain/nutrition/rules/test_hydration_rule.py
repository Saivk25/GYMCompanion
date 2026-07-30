"""Tests for app/domain/nutrition/rules/hydration_rule.py."""

import pytest

from app.domain.nutrition.rules.context import NutritionRuleContext
from app.domain.nutrition.rules.hydration_rule import HydrationRule
from app.domain.nutrition.value_objects import WaterIntake
from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity


@pytest.mark.unit
def test_exposes_id_name_description_severity() -> None:
    rule = HydrationRule()
    assert rule.id == RuleId("nutrition.hydration")
    assert rule.name == "Hydration"
    assert rule.description
    assert rule.severity == RecommendationSeverity.WARNING


@pytest.mark.unit
def test_passes_with_no_data() -> None:
    result = HydrationRule().evaluate(NutritionRuleContext())
    assert result.passed is True
    assert result.triggered_rules == ()


@pytest.mark.unit
def test_passes_within_the_default_range() -> None:
    result = HydrationRule().evaluate(NutritionRuleContext(water_intake=WaterIntake(2500.0)))
    assert result.passed is True


@pytest.mark.unit
def test_fails_below_the_minimum() -> None:
    rule = HydrationRule()
    result = rule.evaluate(NutritionRuleContext(water_intake=WaterIntake(500.0)))
    assert result.passed is False
    assert result.triggered_rules == (rule.id,)
    assert len(result.recommendations) == 1


@pytest.mark.unit
def test_fails_above_the_maximum() -> None:
    rule = HydrationRule()
    result = rule.evaluate(NutritionRuleContext(water_intake=WaterIntake(7000.0)))
    assert result.passed is False
    assert len(result.recommendations) == 1


@pytest.mark.unit
def test_thresholds_are_configurable() -> None:
    context = NutritionRuleContext(water_intake=WaterIntake(1000.0))
    assert HydrationRule(minimum_water_intake=500.0).evaluate(context).passed is True
    assert HydrationRule(minimum_water_intake=1500.0).evaluate(context).passed is False


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    context = NutritionRuleContext(water_intake=WaterIntake(500.0))
    rule = HydrationRule()
    assert rule.evaluate(context) == rule.evaluate(context)
