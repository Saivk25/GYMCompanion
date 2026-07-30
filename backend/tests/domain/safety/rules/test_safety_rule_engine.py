"""Tests for app/domain/safety/rules/safety_rule_engine.py."""

import pytest

from app.domain.readiness.value_objects import SorenessLevel, StressLevel
from app.domain.rules.engine import RuleEngine
from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity
from app.domain.safety.rules.contraindication_rule import ContraindicationRule
from app.domain.safety.rules.injury_rule import InjuryRule
from app.domain.safety.rules.readiness_safety_rule import ReadinessSafetyRule
from app.domain.safety.rules.safety_rule_engine import SafetyRuleEngine
from app.domain.safety.rules.soreness_rule import SorenessRule
from app.domain.safety.rules.workload_rule import WorkloadRule
from tests.domain.safety.rules.factories import (
    a_declared_restriction,
    a_readiness_context,
    a_safety_context,
    an_active_injury,
)


@pytest.mark.unit
def test_is_a_rule_engine() -> None:
    assert isinstance(SafetyRuleEngine(), RuleEngine)


@pytest.mark.unit
def test_default_construction_registers_all_five_rules() -> None:
    engine = SafetyRuleEngine()
    rule_types = {type(rule) for rule in engine.rules}
    expected_rule_types: set[type[object]] = {
        ReadinessSafetyRule,
        SorenessRule,
        WorkloadRule,
        ContraindicationRule,
        InjuryRule,
    }
    assert rule_types == expected_rule_types
    assert len(engine.rules) == 5


@pytest.mark.unit
def test_accepts_a_custom_rule_set() -> None:
    custom_rule = ReadinessSafetyRule(rule_id=RuleId("custom.readiness"))
    engine = SafetyRuleEngine([custom_rule])
    assert engine.rules == (custom_rule,)


# --- evaluate(): a fully safe context ---


@pytest.mark.unit
def test_evaluating_an_empty_context_passes() -> None:
    result = SafetyRuleEngine().evaluate(a_safety_context())
    assert result.passed is True
    assert result.triggered_rules == ()


@pytest.mark.unit
def test_evaluating_a_safe_readiness_check_in_passes() -> None:
    readiness = a_readiness_context(stress_level=StressLevel(3), soreness_level=SorenessLevel(2))
    result = SafetyRuleEngine().evaluate(a_safety_context(readiness=readiness))
    assert result.passed is True


# --- evaluate(): multiple red flags at once ---


@pytest.mark.unit
def test_evaluating_a_context_with_multiple_red_flags_triggers_all_of_them() -> None:
    readiness = a_readiness_context(stress_level=StressLevel(10), soreness_level=SorenessLevel(10))
    context = a_safety_context(
        readiness=readiness,
        declared_restrictions=(a_declared_restriction(),),
        active_injuries=(an_active_injury(),),
    )

    result = SafetyRuleEngine().evaluate(context)

    assert result.passed is False
    assert RuleId("safety.readiness") in result.triggered_rules
    assert RuleId("safety.soreness") in result.triggered_rules
    assert RuleId("safety.contraindication") in result.triggered_rules
    assert RuleId("safety.injury") in result.triggered_rules
    # WorkloadRule needs recent_training data, not supplied here, so it
    # cannot trigger regardless of severity.
    assert RuleId("safety.workload") not in result.triggered_rules


@pytest.mark.unit
def test_aggregate_severity_is_the_highest_among_triggered_rules() -> None:
    """InjuryRule (CRITICAL) should dominate the aggregate severity even
    though other, lower-severity rules also exist in the default set."""
    context = a_safety_context(active_injuries=(an_active_injury(),))
    result = SafetyRuleEngine().evaluate(context)
    assert result.severity == RecommendationSeverity.CRITICAL


# --- determinism / side-effect freedom ---


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    context = a_safety_context(active_injuries=(an_active_injury(),))
    engine = SafetyRuleEngine()
    assert engine.evaluate(context) == engine.evaluate(context)


@pytest.mark.unit
def test_evaluate_does_not_mutate_the_context() -> None:
    injuries = (an_active_injury(),)
    context = a_safety_context(active_injuries=injuries)
    SafetyRuleEngine().evaluate(context)
    assert context.active_injuries == injuries
