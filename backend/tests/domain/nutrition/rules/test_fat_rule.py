"""Tests for app/domain/nutrition/rules/fat_rule.py."""

import pytest

from app.domain.nutrition.rules.context import NutritionRuleContext
from app.domain.nutrition.rules.fat_rule import FatRule
from app.domain.nutrition.value_objects import Fat
from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity


@pytest.mark.unit
def test_exposes_id_name_description_severity() -> None:
    rule = FatRule()
    assert rule.id == RuleId("nutrition.fat")
    assert rule.name == "Fat"
    assert rule.description
    assert rule.severity == RecommendationSeverity.WARNING


@pytest.mark.unit
def test_passes_with_no_data() -> None:
    result = FatRule().evaluate(NutritionRuleContext())
    assert result.passed is True
    assert result.triggered_rules == ()


@pytest.mark.unit
def test_passes_within_the_default_range() -> None:
    result = FatRule().evaluate(NutritionRuleContext(fat=Fat(70.0)))
    assert result.passed is True


@pytest.mark.unit
def test_fails_below_the_minimum() -> None:
    rule = FatRule()
    result = rule.evaluate(NutritionRuleContext(fat=Fat(5.0)))
    assert result.passed is False
    assert result.triggered_rules == (rule.id,)
    assert len(result.recommendations) == 1


@pytest.mark.unit
def test_fails_above_the_maximum() -> None:
    rule = FatRule()
    result = rule.evaluate(NutritionRuleContext(fat=Fat(200.0)))
    assert result.passed is False
    assert len(result.recommendations) == 1


@pytest.mark.unit
def test_thresholds_are_configurable() -> None:
    context = NutritionRuleContext(fat=Fat(30.0))
    assert FatRule(minimum_fat=10.0).evaluate(context).passed is True
    assert FatRule(minimum_fat=50.0).evaluate(context).passed is False


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    context = NutritionRuleContext(fat=Fat(5.0))
    rule = FatRule()
    assert rule.evaluate(context) == rule.evaluate(context)
