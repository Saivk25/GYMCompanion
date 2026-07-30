"""Tests for app/domain/training_load/rules/chronic_load_rule.py."""

import pytest

from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity
from app.domain.training_load.rules.chronic_load_rule import ChronicLoadRule
from app.domain.training_load.rules.context import TrainingLoadRuleContext
from tests.domain.training_load.rules.factories import daily_summaries

# --- identity ---


@pytest.mark.unit
def test_default_identity() -> None:
    rule = ChronicLoadRule()
    assert rule.id == RuleId("training_load.chronic_load")
    assert rule.name == "Chronic Load"
    assert rule.severity == RecommendationSeverity.ADVISORY


# --- insufficient data ---


@pytest.mark.unit
def test_passes_with_no_history() -> None:
    rule = ChronicLoadRule()
    result = rule.evaluate(TrainingLoadRuleContext(history=()))
    assert result.passed is True
    assert "at least" in result.explanation


@pytest.mark.unit
def test_passes_with_fewer_than_minimum_entries_in_window() -> None:
    rule = ChronicLoadRule(minimum_entries=14)
    context = TrainingLoadRuleContext.from_summaries(daily_summaries([500.0] * 5))
    result = rule.evaluate(context)
    assert result.passed is True


# --- threshold behavior ---


@pytest.mark.unit
def test_passes_when_within_ceiling() -> None:
    rule = ChronicLoadRule(load_ceiling=4500.0, minimum_entries=14)
    # 28 days x 500 = 14000 total, /4 weeks = 3500/week, under the 4500 ceiling.
    context = TrainingLoadRuleContext.from_summaries(daily_summaries([500.0] * 28))
    result = rule.evaluate(context)
    assert result.passed is True
    assert "within the 4500" in result.explanation


@pytest.mark.unit
def test_fails_when_exceeding_ceiling() -> None:
    rule = ChronicLoadRule(load_ceiling=4000.0, minimum_entries=14)
    # 28 days x 700 = 19600 total, /4 weeks = 4900/week, over the 4000 ceiling.
    context = TrainingLoadRuleContext.from_summaries(daily_summaries([700.0] * 28))
    result = rule.evaluate(context)
    assert result.passed is False
    assert result.triggered_rules == (RuleId("training_load.chronic_load"),)
    assert len(result.recommendations) == 1


# --- determinism ---


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    rule = ChronicLoadRule(minimum_entries=14)
    context = TrainingLoadRuleContext.from_summaries(daily_summaries([500.0] * 28))
    assert rule.evaluate(context) == rule.evaluate(context)
