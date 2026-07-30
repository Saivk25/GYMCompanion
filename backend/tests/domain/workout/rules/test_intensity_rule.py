"""Tests for app/domain/workout/rules/intensity_rule.py."""

from datetime import date

import pytest

from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity
from app.domain.workout.rules.intensity_rule import IntensityRule
from tests.domain.workout.rules.factories import a_context, a_summary

# --- identity ---


@pytest.mark.unit
def test_default_identity() -> None:
    rule = IntensityRule()
    assert rule.id == RuleId("progressive_overload.intensity")
    assert rule.name == "Intensity"
    assert rule.severity == RecommendationSeverity.WARNING


# --- insufficient history ---


@pytest.mark.unit
def test_passes_when_fewer_sessions_than_the_minimum() -> None:
    rule = IntensityRule(minimum_sessions=4)
    context = a_context(sessions=[a_summary(), a_summary()])
    result = rule.evaluate(context)
    assert result.passed is True
    assert "at least 4" in result.explanation


@pytest.mark.unit
def test_passes_when_neither_half_has_load_data() -> None:
    rule = IntensityRule(minimum_sessions=4)
    context = a_context(
        sessions=[a_summary(session_date=date(2026, 1, i), average_load=None) for i in range(1, 5)]
    )
    result = rule.evaluate(context)
    assert result.passed is True
    assert "No recorded load data" in result.explanation


@pytest.mark.unit
def test_passes_when_earlier_half_average_load_is_zero() -> None:
    rule = IntensityRule(minimum_sessions=4)
    context = a_context(
        sessions=[
            a_summary(session_date=date(2026, 1, 1), average_load=0.0),
            a_summary(session_date=date(2026, 1, 2), average_load=0.0),
            a_summary(session_date=date(2026, 1, 3), average_load=50.0),
            a_summary(session_date=date(2026, 1, 4), average_load=50.0),
        ]
    )
    result = rule.evaluate(context)
    assert result.passed is True
    assert "no baseline" in result.explanation


# --- declining intensity ---


@pytest.mark.unit
def test_fails_when_later_average_load_declines_beyond_the_threshold() -> None:
    rule = IntensityRule(minimum_sessions=4, decline_threshold=0.15)
    context = a_context(
        sessions=[
            a_summary(session_date=date(2026, 1, 1), average_load=100.0),
            a_summary(session_date=date(2026, 1, 2), average_load=100.0),
            a_summary(session_date=date(2026, 1, 3), average_load=80.0),
            a_summary(session_date=date(2026, 1, 4), average_load=80.0),
        ]
    )
    result = rule.evaluate(context)
    assert result.passed is False
    assert result.triggered_rules == (RuleId("progressive_overload.intensity"),)


@pytest.mark.unit
def test_passes_when_load_is_stable() -> None:
    rule = IntensityRule(minimum_sessions=4, decline_threshold=0.15)
    context = a_context(
        sessions=[
            a_summary(session_date=date(2026, 1, 1), average_load=100.0),
            a_summary(session_date=date(2026, 1, 2), average_load=100.0),
            a_summary(session_date=date(2026, 1, 3), average_load=95.0),
            a_summary(session_date=date(2026, 1, 4), average_load=95.0),
        ]
    )
    result = rule.evaluate(context)
    assert result.passed is True


@pytest.mark.unit
def test_ignores_sessions_with_no_load_data_when_computing_the_average() -> None:
    rule = IntensityRule(minimum_sessions=4, decline_threshold=0.15)
    context = a_context(
        sessions=[
            a_summary(session_date=date(2026, 1, 1), average_load=100.0),
            a_summary(session_date=date(2026, 1, 2), average_load=None),
            a_summary(session_date=date(2026, 1, 3), average_load=100.0),
            a_summary(session_date=date(2026, 1, 4), average_load=100.0),
        ]
    )
    result = rule.evaluate(context)
    assert result.passed is True


# --- determinism ---


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    rule = IntensityRule()
    context = a_context(sessions=[a_summary(session_date=date(2026, 1, i)) for i in range(1, 6)])
    assert rule.evaluate(context) == rule.evaluate(context)
