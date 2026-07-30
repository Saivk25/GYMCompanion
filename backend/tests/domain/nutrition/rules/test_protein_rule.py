"""Tests for app/domain/nutrition/rules/protein_rule.py."""

import pytest

from app.domain.nutrition.rules.context import NutritionRuleContext
from app.domain.nutrition.rules.protein_rule import ProteinRule
from app.domain.nutrition.value_objects import Protein
from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity


@pytest.mark.unit
def test_exposes_id_name_description_severity() -> None:
    rule = ProteinRule()
    assert rule.id == RuleId("nutrition.protein")
    assert rule.name == "Protein"
    assert rule.description
    assert rule.severity == RecommendationSeverity.WARNING


@pytest.mark.unit
def test_passes_with_no_data() -> None:
    result = ProteinRule().evaluate(NutritionRuleContext())
    assert result.passed is True
    assert result.triggered_rules == ()


@pytest.mark.unit
def test_passes_within_the_default_range() -> None:
    result = ProteinRule().evaluate(NutritionRuleContext(protein=Protein(150.0)))
    assert result.passed is True


@pytest.mark.unit
def test_fails_below_the_minimum() -> None:
    rule = ProteinRule()
    result = rule.evaluate(NutritionRuleContext(protein=Protein(20.0)))
    assert result.passed is False
    assert result.triggered_rules == (rule.id,)
    assert len(result.recommendations) == 1


@pytest.mark.unit
def test_fails_above_the_maximum() -> None:
    rule = ProteinRule()
    result = rule.evaluate(NutritionRuleContext(protein=Protein(300.0)))
    assert result.passed is False
    assert len(result.recommendations) == 1


@pytest.mark.unit
def test_thresholds_are_configurable() -> None:
    context = NutritionRuleContext(protein=Protein(60.0))
    assert ProteinRule(minimum_protein=30.0).evaluate(context).passed is True
    assert ProteinRule(minimum_protein=90.0).evaluate(context).passed is False


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    context = NutritionRuleContext(protein=Protein(20.0))
    rule = ProteinRule()
    assert rule.evaluate(context) == rule.evaluate(context)
