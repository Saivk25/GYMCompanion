"""Tests for app/domain/workout/rules/frequency_rule.py."""

from datetime import date

import pytest

from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity
from app.domain.workout.rules.frequency_rule import FrequencyRule
from tests.domain.workout.rules.factories import a_context, a_summary

# --- identity ---


@pytest.mark.unit
def test_default_identity() -> None:
    rule = FrequencyRule()
    assert rule.id == RuleId("progressive_overload.frequency")
    assert rule.name == "Frequency"
    assert rule.severity == RecommendationSeverity.ADVISORY


# --- insufficient history ---


@pytest.mark.unit
def test_passes_when_fewer_sessions_than_the_minimum() -> None:
    rule = FrequencyRule(minimum_sessions=2)
    context = a_context(sessions=[a_summary()])
    result = rule.evaluate(context)
    assert result.passed is True
    assert "at least 2" in result.explanation


@pytest.mark.unit
def test_passes_when_every_session_shares_the_same_date() -> None:
    rule = FrequencyRule(minimum_sessions=2)
    context = a_context(
        sessions=[
            a_summary(session_date=date(2026, 1, 1)),
            a_summary(session_date=date(2026, 1, 1)),
        ]
    )
    result = rule.evaluate(context)
    assert result.passed is True
    assert "same date" in result.explanation


# --- frequency below/at/above minimum ---


@pytest.mark.unit
def test_fails_when_frequency_is_below_the_minimum() -> None:
    # 2 sessions spanning 28 days = 0.5 sessions/week, below the 2.0 default minimum.
    rule = FrequencyRule(minimum_sessions=2, minimum_sessions_per_week=2.0)
    context = a_context(
        sessions=[
            a_summary(session_date=date(2026, 1, 1)),
            a_summary(session_date=date(2026, 1, 29)),
        ]
    )
    result = rule.evaluate(context)
    assert result.passed is False
    assert result.triggered_rules == (RuleId("progressive_overload.frequency"),)
    assert len(result.recommendations) == 1


@pytest.mark.unit
def test_passes_when_frequency_meets_the_minimum() -> None:
    # 4 sessions spanning 7 days = 4 sessions/week, above the 2.0 default minimum.
    rule = FrequencyRule(minimum_sessions=2, minimum_sessions_per_week=2.0)
    context = a_context(
        sessions=[
            a_summary(session_date=date(2026, 1, 1)),
            a_summary(session_date=date(2026, 1, 3)),
            a_summary(session_date=date(2026, 1, 5)),
            a_summary(session_date=date(2026, 1, 8)),
        ]
    )
    result = rule.evaluate(context)
    assert result.passed is True


# --- determinism ---


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    rule = FrequencyRule()
    context = a_context(sessions=[a_summary(session_date=date(2026, 1, i)) for i in range(1, 6)])
    assert rule.evaluate(context) == rule.evaluate(context)
