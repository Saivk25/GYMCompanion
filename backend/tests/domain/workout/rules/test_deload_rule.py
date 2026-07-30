"""Tests for app/domain/workout/rules/deload_rule.py."""

from datetime import date

import pytest

from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity
from app.domain.workout.rules.deload_rule import DeloadRule
from tests.domain.workout.rules.factories import a_context, a_summary

# --- identity ---


@pytest.mark.unit
def test_default_identity() -> None:
    rule = DeloadRule()
    assert rule.id == RuleId("progressive_overload.deload")
    assert rule.name == "Deload"
    assert rule.severity == RecommendationSeverity.ADVISORY


# --- insufficient history ---


@pytest.mark.unit
def test_passes_when_fewer_sessions_than_the_lookback_window() -> None:
    rule = DeloadRule(lookback_sessions=6)
    context = a_context(sessions=[a_summary() for _ in range(3)])
    result = rule.evaluate(context)
    assert result.passed is True
    assert "at least 6" in result.explanation


@pytest.mark.unit
def test_passes_when_peak_volume_is_zero() -> None:
    rule = DeloadRule(lookback_sessions=3)
    context = a_context(
        sessions=[a_summary(session_date=date(2026, 1, i), total_volume=0.0) for i in range(1, 4)]
    )
    result = rule.evaluate(context)
    assert result.passed is True
    assert "nothing to assess" in result.explanation


# --- sustained overload ---


@pytest.mark.unit
def test_fails_when_every_recent_session_stays_near_peak_volume() -> None:
    rule = DeloadRule(lookback_sessions=3, high_volume_ratio=0.90)
    context = a_context(
        sessions=[
            a_summary(session_date=date(2026, 1, 1), total_volume=1000.0),
            a_summary(session_date=date(2026, 1, 2), total_volume=980.0),
            a_summary(session_date=date(2026, 1, 3), total_volume=1000.0),
            a_summary(session_date=date(2026, 1, 4), total_volume=950.0),
        ]
    )
    result = rule.evaluate(context)
    assert result.passed is False
    assert result.triggered_rules == (RuleId("progressive_overload.deload"),)
    assert len(result.recommendations) == 1


@pytest.mark.unit
def test_passes_when_a_lighter_session_breaks_up_the_recent_window() -> None:
    rule = DeloadRule(lookback_sessions=3, high_volume_ratio=0.90)
    context = a_context(
        sessions=[
            a_summary(session_date=date(2026, 1, 1), total_volume=1000.0),
            a_summary(session_date=date(2026, 1, 2), total_volume=1000.0),
            a_summary(session_date=date(2026, 1, 3), total_volume=400.0),
            a_summary(session_date=date(2026, 1, 4), total_volume=1000.0),
        ]
    )
    result = rule.evaluate(context)
    assert result.passed is True


@pytest.mark.unit
def test_only_considers_the_trailing_lookback_window() -> None:
    rule = DeloadRule(lookback_sessions=2, high_volume_ratio=0.90)
    context = a_context(
        sessions=[
            a_summary(session_date=date(2026, 1, 1), total_volume=100.0),  # far-off low session
            a_summary(session_date=date(2026, 1, 2), total_volume=1000.0),
            a_summary(session_date=date(2026, 1, 3), total_volume=1000.0),
        ]
    )
    result = rule.evaluate(context)
    assert result.passed is False


# --- determinism ---


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    rule = DeloadRule(lookback_sessions=3)
    context = a_context(sessions=[a_summary(session_date=date(2026, 1, i)) for i in range(1, 6)])
    assert rule.evaluate(context) == rule.evaluate(context)
