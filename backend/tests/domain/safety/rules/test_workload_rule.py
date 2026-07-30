"""Tests for app/domain/safety/rules/workload_rule.py."""

from datetime import date

import pytest

from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity
from app.domain.safety.rules.workload_rule import WorkloadRule
from tests.domain.safety.rules.factories import a_safety_context
from tests.domain.workout.rules.factories import a_context as a_progressive_overload_context
from tests.domain.workout.rules.factories import a_summary

# --- identity ---


@pytest.mark.unit
def test_default_identity() -> None:
    rule = WorkloadRule()
    assert rule.id == RuleId("safety.workload")
    assert rule.name == "Workload Safety"
    assert rule.severity == RecommendationSeverity.WARNING


# --- missing / insufficient data ---


@pytest.mark.unit
def test_passes_when_no_recent_training_supplied() -> None:
    rule = WorkloadRule()
    result = rule.evaluate(a_safety_context())
    assert result.passed is True
    assert "No recent training history supplied" in result.explanation


@pytest.mark.unit
def test_passes_when_fewer_sessions_than_required() -> None:
    rule = WorkloadRule(recent_sessions=2, baseline_sessions=6)
    recent_training = a_progressive_overload_context(
        sessions=[a_summary(session_date=date(2026, 1, i)) for i in range(1, 4)]
    )
    context = a_safety_context(recent_training=recent_training)
    result = rule.evaluate(context)
    assert result.passed is True
    assert "at least 8" in result.explanation


@pytest.mark.unit
def test_passes_when_baseline_average_is_zero() -> None:
    rule = WorkloadRule(recent_sessions=2, baseline_sessions=2)
    sessions = [
        a_summary(session_date=date(2026, 1, 1), total_volume=0.0),
        a_summary(session_date=date(2026, 1, 2), total_volume=0.0),
        a_summary(session_date=date(2026, 1, 3), total_volume=500.0),
        a_summary(session_date=date(2026, 1, 4), total_volume=500.0),
    ]
    context = a_safety_context(recent_training=a_progressive_overload_context(sessions=sessions))
    result = rule.evaluate(context)
    assert result.passed is True
    assert "no baseline" in result.explanation


# --- spike detection ---


@pytest.mark.unit
def test_fails_on_a_sharp_volume_spike() -> None:
    rule = WorkloadRule(recent_sessions=2, baseline_sessions=4, spike_ratio_threshold=1.5)
    sessions = [
        a_summary(session_date=date(2026, 1, 1), total_volume=1000.0),
        a_summary(session_date=date(2026, 1, 2), total_volume=1000.0),
        a_summary(session_date=date(2026, 1, 3), total_volume=1000.0),
        a_summary(session_date=date(2026, 1, 4), total_volume=1000.0),
        a_summary(session_date=date(2026, 1, 5), total_volume=2000.0),
        a_summary(session_date=date(2026, 1, 6), total_volume=2000.0),
    ]
    context = a_safety_context(recent_training=a_progressive_overload_context(sessions=sessions))
    result = rule.evaluate(context)
    assert result.passed is False
    assert result.triggered_rules == (RuleId("safety.workload"),)
    assert len(result.recommendations) == 1


@pytest.mark.unit
def test_passes_with_a_gradual_increase() -> None:
    rule = WorkloadRule(recent_sessions=2, baseline_sessions=4, spike_ratio_threshold=1.5)
    sessions = [
        a_summary(session_date=date(2026, 1, 1), total_volume=1000.0),
        a_summary(session_date=date(2026, 1, 2), total_volume=1000.0),
        a_summary(session_date=date(2026, 1, 3), total_volume=1000.0),
        a_summary(session_date=date(2026, 1, 4), total_volume=1000.0),
        a_summary(session_date=date(2026, 1, 5), total_volume=1100.0),
        a_summary(session_date=date(2026, 1, 6), total_volume=1100.0),
    ]
    context = a_safety_context(recent_training=a_progressive_overload_context(sessions=sessions))
    result = rule.evaluate(context)
    assert result.passed is True


# --- determinism ---


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    rule = WorkloadRule(recent_sessions=1, baseline_sessions=2)
    sessions = [a_summary(session_date=date(2026, 1, i)) for i in range(1, 4)]
    context = a_safety_context(recent_training=a_progressive_overload_context(sessions=sessions))
    assert rule.evaluate(context) == rule.evaluate(context)
