"""Tests for app/domain/training_load/rules/strain_rule.py."""

import pytest

from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity
from app.domain.training_load.rules.context import TrainingLoadRuleContext
from app.domain.training_load.rules.strain_rule import StrainRule
from tests.domain.training_load.rules.factories import daily_summaries

# --- identity ---


@pytest.mark.unit
def test_default_identity() -> None:
    rule = StrainRule()
    assert rule.id == RuleId("training_load.strain")
    assert rule.name == "Strain"
    assert rule.severity == RecommendationSeverity.WARNING


# --- insufficient data ---


@pytest.mark.unit
def test_passes_with_no_history() -> None:
    rule = StrainRule()
    result = rule.evaluate(TrainingLoadRuleContext(history=()))
    assert result.passed is True
    assert "at least" in result.explanation


@pytest.mark.unit
def test_passes_when_fewer_than_minimum_entries() -> None:
    rule = StrainRule(minimum_entries=4)
    context = TrainingLoadRuleContext.from_summaries(daily_summaries([500.0, 500.0]))
    result = rule.evaluate(context)
    assert result.passed is True


@pytest.mark.unit
def test_passes_when_mean_load_is_zero() -> None:
    rule = StrainRule(minimum_entries=4)
    context = TrainingLoadRuleContext.from_summaries(daily_summaries([0.0] * 7))
    result = rule.evaluate(context)
    assert result.passed is True
    assert "nothing to evaluate" in result.explanation


# --- strain behavior ---


@pytest.mark.unit
def test_fails_when_load_is_identical_every_day() -> None:
    rule = StrainRule(minimum_entries=4)
    context = TrainingLoadRuleContext.from_summaries(daily_summaries([2000.0] * 7))
    result = rule.evaluate(context)
    assert result.passed is False
    assert result.triggered_rules == (RuleId("training_load.strain"),)
    assert "unbounded" in result.explanation
    assert len(result.recommendations) == 1


@pytest.mark.unit
def test_passes_when_strain_is_within_ceiling() -> None:
    rule = StrainRule(minimum_entries=4, strain_ceiling=10000.0)
    context = TrainingLoadRuleContext.from_summaries(
        daily_summaries([300.0, 100.0, 350.0, 80.0, 250.0, 50.0, 200.0])
    )
    result = rule.evaluate(context)
    assert result.passed is True


@pytest.mark.unit
def test_fails_when_strain_exceeds_ceiling_without_zero_variance() -> None:
    rule = StrainRule(minimum_entries=4, strain_ceiling=5000.0)
    context = TrainingLoadRuleContext.from_summaries(
        daily_summaries([800.0, 300.0, 900.0, 200.0, 700.0, 100.0, 600.0])
    )
    result = rule.evaluate(context)
    assert result.passed is False
    assert "exceeding the 5000" in result.explanation


# --- determinism ---


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    rule = StrainRule(minimum_entries=4)
    context = TrainingLoadRuleContext.from_summaries(
        daily_summaries([800.0, 200.0, 900.0, 100.0, 700.0, 50.0, 600.0])
    )
    assert rule.evaluate(context) == rule.evaluate(context)
