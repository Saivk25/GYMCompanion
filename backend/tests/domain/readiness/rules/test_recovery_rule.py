"""Tests for app/domain/readiness/rules/recovery_rule.py."""

import pytest

from app.domain.readiness.rules.context import ReadinessRuleContext
from app.domain.readiness.rules.recovery_rule import RecoveryRule
from app.domain.readiness.value_objects import HeartRateVariability, RestingHeartRate
from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity


@pytest.mark.unit
def test_exposes_id_name_description_severity() -> None:
    rule = RecoveryRule()
    assert rule.id == RuleId("readiness.recovery_metrics")
    assert rule.name == "Recovery Metrics"
    assert rule.description
    assert rule.severity == RecommendationSeverity.WARNING


@pytest.mark.unit
def test_passes_with_no_data_at_all() -> None:
    result = RecoveryRule().evaluate(ReadinessRuleContext())
    assert result.passed is True
    assert result.triggered_rules == ()


# --- resting heart rate only ---


@pytest.mark.unit
def test_passes_when_only_resting_heart_rate_is_within_range() -> None:
    context = ReadinessRuleContext(resting_heart_rate=RestingHeartRate(60.0))
    assert RecoveryRule().evaluate(context).passed is True


@pytest.mark.unit
def test_fails_when_only_resting_heart_rate_is_elevated() -> None:
    rule = RecoveryRule()
    context = ReadinessRuleContext(resting_heart_rate=RestingHeartRate(80.0))
    result = rule.evaluate(context)
    assert result.passed is False
    assert result.triggered_rules == (rule.id,)
    assert "resting heart rate" in result.explanation.lower()


# --- heart rate variability only ---


@pytest.mark.unit
def test_passes_when_only_heart_rate_variability_is_within_range() -> None:
    context = ReadinessRuleContext(heart_rate_variability=HeartRateVariability(50.0))
    assert RecoveryRule().evaluate(context).passed is True


@pytest.mark.unit
def test_fails_when_only_heart_rate_variability_is_depressed() -> None:
    rule = RecoveryRule()
    context = ReadinessRuleContext(heart_rate_variability=HeartRateVariability(20.0))
    result = rule.evaluate(context)
    assert result.passed is False
    assert "heart rate variability" in result.explanation.lower()


# --- both present ---


@pytest.mark.unit
def test_passes_when_both_are_within_range() -> None:
    context = ReadinessRuleContext(
        resting_heart_rate=RestingHeartRate(55.0),
        heart_rate_variability=HeartRateVariability(60.0),
    )
    assert RecoveryRule().evaluate(context).passed is True


@pytest.mark.unit
def test_fails_and_reports_both_problems_when_both_are_out_of_range() -> None:
    context = ReadinessRuleContext(
        resting_heart_rate=RestingHeartRate(90.0),
        heart_rate_variability=HeartRateVariability(15.0),
    )
    result = RecoveryRule().evaluate(context)
    assert result.passed is False
    assert "resting heart rate" in result.explanation.lower()
    assert "heart rate variability" in result.explanation.lower()


@pytest.mark.unit
def test_failure_carries_a_recommendation() -> None:
    context = ReadinessRuleContext(resting_heart_rate=RestingHeartRate(90.0))
    result = RecoveryRule().evaluate(context)
    assert len(result.recommendations) == 1


# --- configurability ---


@pytest.mark.unit
def test_thresholds_are_configurable() -> None:
    context = ReadinessRuleContext(
        resting_heart_rate=RestingHeartRate(65.0),
        heart_rate_variability=HeartRateVariability(45.0),
    )
    lenient = RecoveryRule(maximum_resting_heart_rate=100.0, minimum_heart_rate_variability=10.0)
    strict = RecoveryRule(maximum_resting_heart_rate=60.0, minimum_heart_rate_variability=50.0)
    assert lenient.evaluate(context).passed is True
    assert strict.evaluate(context).passed is False


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    context = ReadinessRuleContext(resting_heart_rate=RestingHeartRate(90.0))
    rule = RecoveryRule()
    assert rule.evaluate(context) == rule.evaluate(context)
