"""Tests for app/domain/workout/rules/volume_rule.py."""

from datetime import date

import pytest

from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity
from app.domain.workout.rules.volume_rule import VolumeRule
from tests.domain.workout.rules.factories import a_context, a_summary

# --- identity ---


@pytest.mark.unit
def test_default_identity() -> None:
    rule = VolumeRule()
    assert rule.id == RuleId("progressive_overload.volume")
    assert rule.name == "Volume"
    assert rule.severity == RecommendationSeverity.WARNING


@pytest.mark.unit
def test_accepts_a_custom_rule_id() -> None:
    rule = VolumeRule(rule_id=RuleId("custom.volume"))
    assert rule.id == RuleId("custom.volume")


# --- insufficient history ---


@pytest.mark.unit
def test_passes_when_fewer_sessions_than_the_minimum() -> None:
    rule = VolumeRule(minimum_sessions=4)
    context = a_context(sessions=[a_summary(), a_summary()])
    result = rule.evaluate(context)
    assert result.passed is True
    assert "at least 4" in result.explanation


@pytest.mark.unit
def test_passes_when_earlier_half_has_zero_average_volume() -> None:
    rule = VolumeRule(minimum_sessions=4)
    context = a_context(
        sessions=[
            a_summary(session_date=date(2026, 1, 1), total_volume=0.0),
            a_summary(session_date=date(2026, 1, 2), total_volume=0.0),
            a_summary(session_date=date(2026, 1, 3), total_volume=500.0),
            a_summary(session_date=date(2026, 1, 4), total_volume=500.0),
        ]
    )
    result = rule.evaluate(context)
    assert result.passed is True
    assert "no baseline" in result.explanation


# --- declining volume ---


@pytest.mark.unit
def test_fails_when_later_average_volume_declines_beyond_the_threshold() -> None:
    rule = VolumeRule(minimum_sessions=4, decline_threshold=0.20)
    context = a_context(
        sessions=[
            a_summary(session_date=date(2026, 1, 1), total_volume=1000.0),
            a_summary(session_date=date(2026, 1, 2), total_volume=1000.0),
            a_summary(session_date=date(2026, 1, 3), total_volume=700.0),
            a_summary(session_date=date(2026, 1, 4), total_volume=700.0),
        ]
    )
    result = rule.evaluate(context)
    assert result.passed is False
    assert result.triggered_rules == (RuleId("progressive_overload.volume"),)
    assert len(result.recommendations) == 1


@pytest.mark.unit
def test_passes_when_volume_declines_within_the_threshold() -> None:
    rule = VolumeRule(minimum_sessions=4, decline_threshold=0.20)
    context = a_context(
        sessions=[
            a_summary(session_date=date(2026, 1, 1), total_volume=1000.0),
            a_summary(session_date=date(2026, 1, 2), total_volume=1000.0),
            a_summary(session_date=date(2026, 1, 3), total_volume=900.0),
            a_summary(session_date=date(2026, 1, 4), total_volume=900.0),
        ]
    )
    result = rule.evaluate(context)
    assert result.passed is True


@pytest.mark.unit
def test_passes_when_volume_increases() -> None:
    rule = VolumeRule(minimum_sessions=4)
    context = a_context(
        sessions=[
            a_summary(session_date=date(2026, 1, 1), total_volume=1000.0),
            a_summary(session_date=date(2026, 1, 2), total_volume=1000.0),
            a_summary(session_date=date(2026, 1, 3), total_volume=1500.0),
            a_summary(session_date=date(2026, 1, 4), total_volume=1500.0),
        ]
    )
    result = rule.evaluate(context)
    assert result.passed is True


# --- determinism ---


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    rule = VolumeRule()
    context = a_context(sessions=[a_summary(session_date=date(2026, 1, i)) for i in range(1, 6)])
    assert rule.evaluate(context) == rule.evaluate(context)
