"""Tests for app/domain/nutrition/rules/carbohydrates_rule.py."""

import pytest

from app.domain.nutrition.rules.carbohydrates_rule import CarbohydratesRule
from app.domain.nutrition.rules.context import NutritionRuleContext
from app.domain.nutrition.value_objects import Carbohydrates
from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity


@pytest.mark.unit
def test_exposes_id_name_description_severity() -> None:
    rule = CarbohydratesRule()
    assert rule.id == RuleId("nutrition.carbohydrates")
    assert rule.name == "Carbohydrates"
    assert rule.description
    assert rule.severity == RecommendationSeverity.WARNING


@pytest.mark.unit
def test_passes_with_no_data() -> None:
    result = CarbohydratesRule().evaluate(NutritionRuleContext())
    assert result.passed is True
    assert result.triggered_rules == ()


@pytest.mark.unit
def test_passes_within_the_default_range() -> None:
    result = CarbohydratesRule().evaluate(NutritionRuleContext(carbohydrates=Carbohydrates(200.0)))
    assert result.passed is True


@pytest.mark.unit
def test_fails_below_the_minimum() -> None:
    rule = CarbohydratesRule()
    result = rule.evaluate(NutritionRuleContext(carbohydrates=Carbohydrates(10.0)))
    assert result.passed is False
    assert result.triggered_rules == (rule.id,)
    assert len(result.recommendations) == 1


@pytest.mark.unit
def test_fails_above_the_maximum() -> None:
    rule = CarbohydratesRule()
    result = rule.evaluate(NutritionRuleContext(carbohydrates=Carbohydrates(500.0)))
    assert result.passed is False
    assert len(result.recommendations) == 1


@pytest.mark.unit
def test_thresholds_are_configurable() -> None:
    context = NutritionRuleContext(carbohydrates=Carbohydrates(80.0))
    assert CarbohydratesRule(minimum_carbohydrates=50.0).evaluate(context).passed is True
    assert CarbohydratesRule(minimum_carbohydrates=100.0).evaluate(context).passed is False


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    context = NutritionRuleContext(carbohydrates=Carbohydrates(10.0))
    rule = CarbohydratesRule()
    assert rule.evaluate(context) == rule.evaluate(context)
