"""Tests for app/domain/training_load/rules/load_ratio_rule.py."""

from datetime import date, timedelta

import pytest

from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity
from app.domain.training_load.rules.context import TrainingLoadRuleContext
from app.domain.training_load.rules.load_ratio_rule import LoadRatioRule
from tests.domain.training_load.rules.factories import a_training_load_summary, daily_summaries

# --- identity ---


@pytest.mark.unit
def test_default_identity() -> None:
    rule = LoadRatioRule()
    assert rule.id == RuleId("training_load.load_ratio")
    assert rule.name == "Load Ratio"
    assert rule.severity == RecommendationSeverity.WARNING


# --- insufficient data ---


@pytest.mark.unit
def test_passes_with_no_history() -> None:
    rule = LoadRatioRule()
    result = rule.evaluate(TrainingLoadRuleContext(history=()))
    assert result.passed is True
    assert "baseline" in result.explanation


@pytest.mark.unit
def test_passes_when_fewer_than_minimum_chronic_entries() -> None:
    rule = LoadRatioRule(minimum_chronic_entries=14)
    context = TrainingLoadRuleContext.from_summaries(daily_summaries([500.0] * 5))
    result = rule.evaluate(context)
    assert result.passed is True


@pytest.mark.unit
def test_passes_when_chronic_load_is_zero() -> None:
    rule = LoadRatioRule(minimum_chronic_entries=14)
    context = TrainingLoadRuleContext.from_summaries(daily_summaries([0.0] * 28))
    result = rule.evaluate(context)
    assert result.passed is True
    assert "no baseline" in result.explanation


# --- ratio behavior ---


def _build(
    *, baseline_days: int, baseline_load: float, spike_days: int, spike_load: float
) -> TrainingLoadRuleContext:
    start = date(2026, 1, 1)
    history = [
        a_training_load_summary(load_date=start + timedelta(days=i), load=baseline_load)
        for i in range(baseline_days)
    ] + [
        a_training_load_summary(
            load_date=start + timedelta(days=baseline_days + i), load=spike_load
        )
        for i in range(spike_days)
    ]
    return TrainingLoadRuleContext.from_summaries(history)


@pytest.mark.unit
def test_passes_when_ratio_is_within_range() -> None:
    rule = LoadRatioRule(minimum_chronic_entries=14)
    context = _build(baseline_days=21, baseline_load=500.0, spike_days=7, spike_load=550.0)
    result = rule.evaluate(context)
    assert result.passed is True


@pytest.mark.unit
def test_fails_when_ratio_is_above_high_threshold() -> None:
    rule = LoadRatioRule(minimum_chronic_entries=14, high_ratio_threshold=1.5)
    context = _build(baseline_days=21, baseline_load=500.0, spike_days=7, spike_load=1500.0)
    result = rule.evaluate(context)
    assert result.passed is False
    assert result.triggered_rules == (RuleId("training_load.load_ratio"),)
    assert "high-risk" in result.explanation


@pytest.mark.unit
def test_fails_when_ratio_is_below_low_threshold() -> None:
    rule = LoadRatioRule(minimum_chronic_entries=14, low_ratio_threshold=0.8)
    context = _build(baseline_days=21, baseline_load=1000.0, spike_days=7, spike_load=50.0)
    result = rule.evaluate(context)
    assert result.passed is False
    assert result.triggered_rules == (RuleId("training_load.load_ratio"),)
    assert "below the" in result.explanation


# --- determinism ---


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    rule = LoadRatioRule(minimum_chronic_entries=14)
    context = _build(baseline_days=21, baseline_load=500.0, spike_days=7, spike_load=1500.0)
    assert rule.evaluate(context) == rule.evaluate(context)
