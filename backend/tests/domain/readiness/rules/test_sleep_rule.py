"""Tests for app/domain/readiness/rules/sleep_rule.py."""

from datetime import timedelta

import pytest

from app.domain.readiness.rules.context import ReadinessRuleContext
from app.domain.readiness.rules.sleep_rule import SleepRule
from app.domain.readiness.value_objects import SleepDuration
from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity


@pytest.mark.unit
def test_exposes_id_name_description_severity() -> None:
    rule = SleepRule()
    assert rule.id == RuleId("readiness.sleep_duration")
    assert rule.name == "Sleep Duration"
    assert rule.description
    assert rule.severity == RecommendationSeverity.WARNING


@pytest.mark.unit
def test_passes_with_no_data() -> None:
    result = SleepRule().evaluate(ReadinessRuleContext())
    assert result.passed is True
    assert result.triggered_rules == ()


@pytest.mark.unit
def test_passes_when_sleep_meets_the_minimum() -> None:
    context = ReadinessRuleContext(sleep_duration=SleepDuration(timedelta(hours=7)))
    result = SleepRule().evaluate(context)
    assert result.passed is True


@pytest.mark.unit
def test_passes_at_exactly_the_minimum() -> None:
    context = ReadinessRuleContext(sleep_duration=SleepDuration(timedelta(hours=7)))
    result = SleepRule(minimum_sleep=timedelta(hours=7)).evaluate(context)
    assert result.passed is True


@pytest.mark.unit
def test_fails_when_sleep_is_below_the_minimum() -> None:
    context = ReadinessRuleContext(sleep_duration=SleepDuration(timedelta(hours=5)))
    rule = SleepRule()
    result = rule.evaluate(context)
    assert result.passed is False
    assert result.triggered_rules == (rule.id,)
    assert result.severity == RecommendationSeverity.WARNING


@pytest.mark.unit
def test_failure_carries_a_recommendation() -> None:
    context = ReadinessRuleContext(sleep_duration=SleepDuration(timedelta(hours=4)))
    result = SleepRule().evaluate(context)
    assert len(result.recommendations) == 1
    assert result.recommendations[0].severity == RecommendationSeverity.WARNING


@pytest.mark.unit
def test_minimum_sleep_is_configurable() -> None:
    context = ReadinessRuleContext(sleep_duration=SleepDuration(timedelta(hours=6)))
    lenient_rule = SleepRule(minimum_sleep=timedelta(hours=5))
    strict_rule = SleepRule(minimum_sleep=timedelta(hours=8))
    assert lenient_rule.evaluate(context).passed is True
    assert strict_rule.evaluate(context).passed is False


@pytest.mark.unit
def test_severity_is_configurable() -> None:
    context = ReadinessRuleContext(sleep_duration=SleepDuration(timedelta(hours=2)))
    rule = SleepRule(severity=RecommendationSeverity.CRITICAL)
    result = rule.evaluate(context)
    assert result.severity == RecommendationSeverity.CRITICAL


@pytest.mark.unit
def test_rule_id_is_configurable() -> None:
    rule = SleepRule(rule_id=RuleId("custom.sleep"))
    assert rule.id == RuleId("custom.sleep")


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    context = ReadinessRuleContext(sleep_duration=SleepDuration(timedelta(hours=5)))
    rule = SleepRule()
    assert rule.evaluate(context) == rule.evaluate(context)
