"""Tests for app/domain/safety/rules/readiness_safety_rule.py."""

from datetime import timedelta

import pytest

from app.domain.readiness.value_objects import (
    HeartRateVariability,
    RestingHeartRate,
    SleepDuration,
    StressLevel,
)
from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity
from app.domain.safety.rules.readiness_safety_rule import ReadinessSafetyRule
from tests.domain.safety.rules.factories import a_readiness_context, a_safety_context

# --- identity ---


@pytest.mark.unit
def test_default_identity() -> None:
    rule = ReadinessSafetyRule()
    assert rule.id == RuleId("safety.readiness")
    assert rule.name == "Readiness Safety"
    assert rule.severity == RecommendationSeverity.CRITICAL


# --- missing data ---


@pytest.mark.unit
def test_passes_when_no_readiness_supplied() -> None:
    rule = ReadinessSafetyRule()
    result = rule.evaluate(a_safety_context())
    assert result.passed is True
    assert "No readiness check-in supplied" in result.explanation


@pytest.mark.unit
def test_passes_when_readiness_has_no_relevant_fields_recorded() -> None:
    rule = ReadinessSafetyRule()
    context = a_safety_context(readiness=a_readiness_context())
    result = rule.evaluate(context)
    assert result.passed is True


# --- individual red flags ---


@pytest.mark.unit
def test_fails_on_critically_low_sleep() -> None:
    rule = ReadinessSafetyRule(critical_minimum_sleep=timedelta(hours=3))
    context = a_safety_context(
        readiness=a_readiness_context(sleep_duration=SleepDuration(timedelta(hours=2)))
    )
    result = rule.evaluate(context)
    assert result.passed is False
    assert result.triggered_rules == (RuleId("safety.readiness"),)
    assert len(result.recommendations) == 1


@pytest.mark.unit
def test_passes_when_sleep_is_above_the_critical_threshold() -> None:
    rule = ReadinessSafetyRule(critical_minimum_sleep=timedelta(hours=3))
    context = a_safety_context(
        readiness=a_readiness_context(sleep_duration=SleepDuration(timedelta(hours=6)))
    )
    result = rule.evaluate(context)
    assert result.passed is True


@pytest.mark.unit
def test_fails_on_critically_high_stress() -> None:
    rule = ReadinessSafetyRule(critical_stress=9)
    context = a_safety_context(readiness=a_readiness_context(stress_level=StressLevel(9)))
    result = rule.evaluate(context)
    assert result.passed is False


@pytest.mark.unit
def test_passes_when_stress_is_below_the_critical_threshold() -> None:
    rule = ReadinessSafetyRule(critical_stress=9)
    context = a_safety_context(readiness=a_readiness_context(stress_level=StressLevel(5)))
    result = rule.evaluate(context)
    assert result.passed is True


@pytest.mark.unit
def test_fails_on_critical_resting_heart_rate_and_hrv_combination() -> None:
    rule = ReadinessSafetyRule(
        critical_resting_heart_rate=100.0, critical_heart_rate_variability=20.0
    )
    context = a_safety_context(
        readiness=a_readiness_context(
            resting_heart_rate=RestingHeartRate(110.0),
            heart_rate_variability=HeartRateVariability(15.0),
        )
    )
    result = rule.evaluate(context)
    assert result.passed is False


@pytest.mark.unit
def test_passes_when_only_one_of_heart_rate_or_hrv_is_critical() -> None:
    """Both must be critical together — a high resting heart rate alone,
    with normal HRV, is not treated as a red flag by this rule."""
    rule = ReadinessSafetyRule(
        critical_resting_heart_rate=100.0, critical_heart_rate_variability=20.0
    )
    context = a_safety_context(
        readiness=a_readiness_context(
            resting_heart_rate=RestingHeartRate(110.0),
            heart_rate_variability=HeartRateVariability(50.0),
        )
    )
    result = rule.evaluate(context)
    assert result.passed is True


@pytest.mark.unit
def test_passes_when_heart_rate_present_but_hrv_missing() -> None:
    rule = ReadinessSafetyRule()
    context = a_safety_context(
        readiness=a_readiness_context(resting_heart_rate=RestingHeartRate(110.0))
    )
    result = rule.evaluate(context)
    assert result.passed is True


# --- multiple red flags at once ---


@pytest.mark.unit
def test_reports_multiple_problems_together() -> None:
    rule = ReadinessSafetyRule(critical_minimum_sleep=timedelta(hours=3), critical_stress=9)
    context = a_safety_context(
        readiness=a_readiness_context(
            sleep_duration=SleepDuration(timedelta(hours=1)),
            stress_level=StressLevel(10),
        )
    )
    result = rule.evaluate(context)
    assert result.passed is False
    assert "sleep" in result.explanation
    assert "stress" in result.explanation


# --- determinism ---


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    rule = ReadinessSafetyRule()
    context = a_safety_context(readiness=a_readiness_context(stress_level=StressLevel(9)))
    assert rule.evaluate(context) == rule.evaluate(context)
