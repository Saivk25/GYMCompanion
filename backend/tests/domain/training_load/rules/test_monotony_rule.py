"""Tests for app/domain/training_load/rules/monotony_rule.py."""

import pytest

from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity
from app.domain.training_load.rules.context import TrainingLoadRuleContext
from app.domain.training_load.rules.monotony_rule import MonotonyRule
from tests.domain.training_load.rules.factories import daily_summaries

# --- identity ---


@pytest.mark.unit
def test_default_identity() -> None:
    rule = MonotonyRule()
    assert rule.id == RuleId("training_load.monotony")
    assert rule.name == "Monotony"
    assert rule.severity == RecommendationSeverity.WARNING


# --- insufficient data ---


@pytest.mark.unit
def test_passes_with_no_history() -> None:
    rule = MonotonyRule()
    result = rule.evaluate(TrainingLoadRuleContext(history=()))
    assert result.passed is True
    assert "at least" in result.explanation


@pytest.mark.unit
def test_passes_when_fewer_than_minimum_entries() -> None:
    rule = MonotonyRule(minimum_entries=4)
    context = TrainingLoadRuleContext.from_summaries(daily_summaries([500.0, 500.0]))
    result = rule.evaluate(context)
    assert result.passed is True


@pytest.mark.unit
def test_passes_when_mean_load_is_zero() -> None:
    rule = MonotonyRule(minimum_entries=4)
    context = TrainingLoadRuleContext.from_summaries(daily_summaries([0.0] * 7))
    result = rule.evaluate(context)
    assert result.passed is True
    assert "nothing to evaluate" in result.explanation


# --- monotony behavior ---


@pytest.mark.unit
def test_fails_when_load_is_identical_every_day() -> None:
    rule = MonotonyRule(minimum_entries=4)
    context = TrainingLoadRuleContext.from_summaries(daily_summaries([500.0] * 7))
    result = rule.evaluate(context)
    assert result.passed is False
    assert result.triggered_rules == (RuleId("training_load.monotony"),)
    assert "zero variability" in result.explanation
    assert len(result.recommendations) == 1


@pytest.mark.unit
def test_passes_when_variability_is_high() -> None:
    rule = MonotonyRule(minimum_entries=4, monotony_ceiling=2.0)
    context = TrainingLoadRuleContext.from_summaries(
        daily_summaries([800.0, 200.0, 900.0, 100.0, 700.0, 50.0, 600.0])
    )
    result = rule.evaluate(context)
    assert result.passed is True


@pytest.mark.unit
def test_fails_when_monotony_exceeds_ceiling_without_zero_variance() -> None:
    rule = MonotonyRule(minimum_entries=4, monotony_ceiling=1.5)
    # Small variation around a high mean -> high monotony, but not exactly zero variance.
    context = TrainingLoadRuleContext.from_summaries(
        daily_summaries([500.0, 505.0, 495.0, 500.0, 505.0, 495.0, 500.0])
    )
    result = rule.evaluate(context)
    assert result.passed is False
    assert "exceeding the 1.50 ceiling" in result.explanation


# --- determinism ---


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    rule = MonotonyRule(minimum_entries=4)
    context = TrainingLoadRuleContext.from_summaries(
        daily_summaries([800.0, 200.0, 900.0, 100.0, 700.0, 50.0, 600.0])
    )
    assert rule.evaluate(context) == rule.evaluate(context)
