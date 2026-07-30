"""Tests for app/domain/training_load/rules/acute_load_rule.py."""

import pytest

from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity
from app.domain.training_load.rules.acute_load_rule import AcuteLoadRule
from app.domain.training_load.rules.context import TrainingLoadRuleContext
from tests.domain.training_load.rules.factories import daily_summaries

# --- identity ---


@pytest.mark.unit
def test_default_identity() -> None:
    rule = AcuteLoadRule()
    assert rule.id == RuleId("training_load.acute_load")
    assert rule.name == "Acute Load"
    assert rule.severity == RecommendationSeverity.WARNING


# --- insufficient data ---


@pytest.mark.unit
def test_passes_with_no_history() -> None:
    rule = AcuteLoadRule()
    result = rule.evaluate(TrainingLoadRuleContext(history=()))
    assert result.passed is True
    assert "at least" in result.explanation


@pytest.mark.unit
def test_passes_with_fewer_than_minimum_entries_in_window() -> None:
    rule = AcuteLoadRule(minimum_entries=3)
    context = TrainingLoadRuleContext.from_summaries(daily_summaries([500.0, 500.0]))
    result = rule.evaluate(context)
    assert result.passed is True


# --- threshold behavior ---


@pytest.mark.unit
def test_passes_when_within_ceiling() -> None:
    rule = AcuteLoadRule(load_ceiling=5000.0)
    context = TrainingLoadRuleContext.from_summaries(daily_summaries([500.0] * 7))
    result = rule.evaluate(context)
    assert result.passed is True
    assert "within the 5000" in result.explanation


@pytest.mark.unit
def test_fails_when_exceeding_ceiling() -> None:
    rule = AcuteLoadRule(load_ceiling=3000.0)
    context = TrainingLoadRuleContext.from_summaries(daily_summaries([600.0] * 7))
    result = rule.evaluate(context)
    assert result.passed is False
    assert result.triggered_rules == (RuleId("training_load.acute_load"),)
    assert len(result.recommendations) == 1
    assert "exceeding the 3000" in result.explanation


@pytest.mark.unit
def test_only_considers_entries_in_the_window() -> None:
    rule = AcuteLoadRule(window_days=7, load_ceiling=1000.0, minimum_entries=3)
    # 10 days of heavy load, but only the trailing 7 count toward the window.
    context = TrainingLoadRuleContext.from_summaries(daily_summaries([100.0] * 10))
    result = rule.evaluate(context)
    # 7 days x 100.0 = 700, within the 1000 ceiling.
    assert result.passed is True


# --- determinism ---


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    rule = AcuteLoadRule()
    context = TrainingLoadRuleContext.from_summaries(daily_summaries([500.0] * 7))
    assert rule.evaluate(context) == rule.evaluate(context)
