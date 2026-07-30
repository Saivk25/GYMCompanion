"""Tests for app/domain/workout/rules/progression_rule.py."""

from datetime import date

import pytest

from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity
from app.domain.workout.rules.progression_rule import ProgressionRule
from tests.domain.workout.rules.factories import a_context, a_summary

# --- identity ---


@pytest.mark.unit
def test_default_identity() -> None:
    rule = ProgressionRule()
    assert rule.id == RuleId("progressive_overload.progression")
    assert rule.name == "Progression"
    assert rule.severity == RecommendationSeverity.WARNING


# --- insufficient history ---


@pytest.mark.unit
def test_passes_when_fewer_sessions_than_the_minimum() -> None:
    rule = ProgressionRule(minimum_sessions=4)
    context = a_context(sessions=[a_summary(), a_summary()])
    result = rule.evaluate(context)
    assert result.passed is True
    assert "at least 4" in result.explanation


# --- plateau detection ---


@pytest.mark.unit
def test_fails_when_neither_volume_nor_load_reaches_a_new_peak() -> None:
    rule = ProgressionRule(minimum_sessions=4, minimum_growth=0.05)
    context = a_context(
        sessions=[
            a_summary(session_date=date(2026, 1, 1), total_volume=1000.0, average_load=100.0),
            a_summary(session_date=date(2026, 1, 2), total_volume=1000.0, average_load=100.0),
            a_summary(session_date=date(2026, 1, 3), total_volume=1000.0, average_load=100.0),
            a_summary(session_date=date(2026, 1, 4), total_volume=1000.0, average_load=100.0),
        ]
    )
    result = rule.evaluate(context)
    assert result.passed is False
    assert result.triggered_rules == (RuleId("progressive_overload.progression"),)
    assert len(result.recommendations) == 1


@pytest.mark.unit
def test_passes_when_peak_volume_grows_enough() -> None:
    rule = ProgressionRule(minimum_sessions=4, minimum_growth=0.05)
    context = a_context(
        sessions=[
            a_summary(session_date=date(2026, 1, 1), total_volume=1000.0, average_load=100.0),
            a_summary(session_date=date(2026, 1, 2), total_volume=1000.0, average_load=100.0),
            a_summary(session_date=date(2026, 1, 3), total_volume=1200.0, average_load=100.0),
            a_summary(session_date=date(2026, 1, 4), total_volume=1200.0, average_load=100.0),
        ]
    )
    result = rule.evaluate(context)
    assert result.passed is True


@pytest.mark.unit
def test_passes_when_peak_load_grows_enough_even_if_volume_does_not() -> None:
    rule = ProgressionRule(minimum_sessions=4, minimum_growth=0.05)
    context = a_context(
        sessions=[
            a_summary(session_date=date(2026, 1, 1), total_volume=1000.0, average_load=100.0),
            a_summary(session_date=date(2026, 1, 2), total_volume=1000.0, average_load=100.0),
            a_summary(session_date=date(2026, 1, 3), total_volume=1000.0, average_load=120.0),
            a_summary(session_date=date(2026, 1, 4), total_volume=1000.0, average_load=120.0),
        ]
    )
    result = rule.evaluate(context)
    assert result.passed is True


@pytest.mark.unit
def test_fails_when_earlier_peak_volume_is_zero_and_load_shows_no_growth() -> None:
    rule = ProgressionRule(minimum_sessions=4, minimum_growth=0.05)
    context = a_context(
        sessions=[
            a_summary(session_date=date(2026, 1, 1), total_volume=0.0, average_load=None),
            a_summary(session_date=date(2026, 1, 2), total_volume=0.0, average_load=None),
            a_summary(session_date=date(2026, 1, 3), total_volume=0.0, average_load=None),
            a_summary(session_date=date(2026, 1, 4), total_volume=0.0, average_load=None),
        ]
    )
    result = rule.evaluate(context)
    assert result.passed is False


# --- determinism ---


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    rule = ProgressionRule()
    context = a_context(sessions=[a_summary(session_date=date(2026, 1, i)) for i in range(1, 6)])
    assert rule.evaluate(context) == rule.evaluate(context)
