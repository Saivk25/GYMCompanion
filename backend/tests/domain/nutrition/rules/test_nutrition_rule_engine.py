"""Tests for app/domain/nutrition/rules/nutrition_rule_engine.py."""

import pytest

from app.domain.nutrition.rules.calories_rule import CaloriesRule
from app.domain.nutrition.rules.carbohydrates_rule import CarbohydratesRule
from app.domain.nutrition.rules.context import NutritionRuleContext
from app.domain.nutrition.rules.fat_rule import FatRule
from app.domain.nutrition.rules.fiber_rule import FiberRule
from app.domain.nutrition.rules.hydration_rule import HydrationRule
from app.domain.nutrition.rules.nutrition_rule_engine import NutritionRuleEngine
from app.domain.nutrition.rules.protein_rule import ProteinRule
from app.domain.nutrition.value_objects import (
    Calories,
    Carbohydrates,
    Fat,
    Fiber,
    Protein,
    WaterIntake,
)
from app.domain.rules.engine import RuleEngine
from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity


@pytest.mark.unit
def test_is_a_rule_engine() -> None:
    assert isinstance(NutritionRuleEngine(), RuleEngine)


@pytest.mark.unit
def test_default_construction_registers_all_six_rules() -> None:
    engine = NutritionRuleEngine()
    rule_types = {type(rule) for rule in engine.rules}
    expected_rule_types: set[type[object]] = {
        CaloriesRule,
        ProteinRule,
        CarbohydratesRule,
        FatRule,
        FiberRule,
        HydrationRule,
    }
    assert rule_types == expected_rule_types
    assert len(engine.rules) == 6


@pytest.mark.unit
def test_accepts_a_custom_rule_set() -> None:
    custom_rule = CaloriesRule(rule_id=RuleId("custom.calories"))
    engine = NutritionRuleEngine([custom_rule])
    assert engine.rules == (custom_rule,)


# --- evaluate(): empty context ---


@pytest.mark.unit
def test_evaluating_an_empty_context_passes_with_no_findings() -> None:
    result = NutritionRuleEngine().evaluate(NutritionRuleContext())
    assert result.passed is True
    assert result.severity == RecommendationSeverity.INFO
    assert result.triggered_rules == ()
    assert result.recommendations == ()


# --- evaluate(): a fully healthy context ---


@pytest.mark.unit
def test_evaluating_a_fully_healthy_context_passes() -> None:
    context = NutritionRuleContext(
        calories=Calories(2200.0),
        protein=Protein(150.0),
        carbohydrates=Carbohydrates(250.0),
        fat=Fat(70.0),
        fiber=Fiber(25.0),
        water_intake=WaterIntake(2500.0),
    )
    result = NutritionRuleEngine().evaluate(context)
    assert result.passed is True
    assert result.triggered_rules == ()


# --- evaluate(): a poor-nutrition context triggers multiple rules ---


@pytest.mark.unit
def test_evaluating_a_poor_nutrition_context_triggers_every_rule() -> None:
    context = NutritionRuleContext(
        calories=Calories(500.0),
        protein=Protein(10.0),
        carbohydrates=Carbohydrates(10.0),
        fat=Fat(5.0),
        fiber=Fiber(2.0),
        water_intake=WaterIntake(300.0),
    )
    result = NutritionRuleEngine().evaluate(context)

    assert result.passed is False
    assert len(result.triggered_rules) == 6
    assert {str(rule_id) for rule_id in result.triggered_rules} == {
        "nutrition.calories",
        "nutrition.protein",
        "nutrition.carbohydrates",
        "nutrition.fat",
        "nutrition.fiber",
        "nutrition.hydration",
    }
    assert result.severity == RecommendationSeverity.WARNING
    assert len(result.recommendations) == 6


@pytest.mark.unit
def test_evaluating_a_partially_poor_context_only_triggers_the_relevant_rules() -> None:
    context = NutritionRuleContext(
        calories=Calories(2200.0),
        protein=Protein(5.0),
    )
    result = NutritionRuleEngine().evaluate(context)

    assert result.passed is False
    assert result.triggered_rules == (RuleId("nutrition.protein"),)


# --- determinism / side-effect freedom ---


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    engine = NutritionRuleEngine()
    context = NutritionRuleContext(protein=Protein(10.0))
    assert engine.evaluate(context) == engine.evaluate(context)


@pytest.mark.unit
def test_evaluate_does_not_mutate_the_context() -> None:
    context = NutritionRuleContext(protein=Protein(10.0))
    NutritionRuleEngine().evaluate(context)
    assert context.protein == Protein(10.0)
