"""Tests for app/domain/readiness/rules/readiness_rule_engine.py."""

from datetime import timedelta

import pytest

from app.domain.readiness.rules.context import ReadinessRuleContext
from app.domain.readiness.rules.energy_rule import EnergyRule
from app.domain.readiness.rules.readiness_rule_engine import ReadinessRuleEngine
from app.domain.readiness.rules.recovery_rule import RecoveryRule
from app.domain.readiness.rules.sleep_rule import SleepRule
from app.domain.readiness.rules.soreness_rule import SorenessRule
from app.domain.readiness.rules.stress_rule import StressRule
from app.domain.readiness.value_objects import (
    EnergyLevel,
    HeartRateVariability,
    RestingHeartRate,
    SleepDuration,
    SorenessLevel,
    StressLevel,
)
from app.domain.rules.engine import RuleEngine
from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity


@pytest.mark.unit
def test_is_a_rule_engine() -> None:
    assert isinstance(ReadinessRuleEngine(), RuleEngine)


@pytest.mark.unit
def test_default_construction_registers_all_five_rules() -> None:
    engine = ReadinessRuleEngine()
    rule_types = {type(rule) for rule in engine.rules}
    assert rule_types == {SleepRule, EnergyRule, StressRule, SorenessRule, RecoveryRule}
    assert len(engine.rules) == 5


@pytest.mark.unit
def test_accepts_a_custom_rule_set() -> None:
    custom_rule = SleepRule(rule_id=RuleId("custom.sleep"))
    engine = ReadinessRuleEngine([custom_rule])
    assert engine.rules == (custom_rule,)


# --- evaluate(): empty context ---


@pytest.mark.unit
def test_evaluating_an_empty_context_passes_with_no_findings() -> None:
    result = ReadinessRuleEngine().evaluate(ReadinessRuleContext())
    assert result.passed is True
    assert result.severity == RecommendationSeverity.INFO
    assert result.triggered_rules == ()
    assert result.recommendations == ()


# --- evaluate(): a fully healthy context ---


@pytest.mark.unit
def test_evaluating_a_fully_healthy_context_passes() -> None:
    context = ReadinessRuleContext(
        sleep_duration=SleepDuration(timedelta(hours=8)),
        energy_level=EnergyLevel(8),
        stress_level=StressLevel(2),
        soreness_level=SorenessLevel(2),
        resting_heart_rate=RestingHeartRate(55.0),
        heart_rate_variability=HeartRateVariability(60.0),
    )
    result = ReadinessRuleEngine().evaluate(context)
    assert result.passed is True
    assert result.triggered_rules == ()


# --- evaluate(): a poor-readiness context triggers multiple rules ---


@pytest.mark.unit
def test_evaluating_a_poor_readiness_context_triggers_every_rule() -> None:
    context = ReadinessRuleContext(
        sleep_duration=SleepDuration(timedelta(hours=4)),
        energy_level=EnergyLevel(2),
        stress_level=StressLevel(9),
        soreness_level=SorenessLevel(9),
        resting_heart_rate=RestingHeartRate(90.0),
        heart_rate_variability=HeartRateVariability(15.0),
    )
    result = ReadinessRuleEngine().evaluate(context)

    assert result.passed is False
    assert len(result.triggered_rules) == 5
    assert {str(rule_id) for rule_id in result.triggered_rules} == {
        "readiness.sleep_duration",
        "readiness.energy_level",
        "readiness.stress_level",
        "readiness.soreness_level",
        "readiness.recovery_metrics",
    }
    assert result.severity == RecommendationSeverity.WARNING
    assert len(result.recommendations) == 5


@pytest.mark.unit
def test_evaluating_a_partially_poor_context_only_triggers_the_relevant_rules() -> None:
    context = ReadinessRuleContext(
        sleep_duration=SleepDuration(timedelta(hours=8)),
        energy_level=EnergyLevel(1),
    )
    result = ReadinessRuleEngine().evaluate(context)

    assert result.passed is False
    assert result.triggered_rules == (RuleId("readiness.energy_level"),)


# --- determinism / side-effect freedom ---


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    engine = ReadinessRuleEngine()
    context = ReadinessRuleContext(energy_level=EnergyLevel(3))
    assert engine.evaluate(context) == engine.evaluate(context)


@pytest.mark.unit
def test_evaluate_does_not_mutate_the_context() -> None:
    context = ReadinessRuleContext(energy_level=EnergyLevel(3))
    ReadinessRuleEngine().evaluate(context)
    assert context.energy_level == EnergyLevel(3)
