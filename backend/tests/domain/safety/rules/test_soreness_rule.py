"""Tests for app/domain/safety/rules/soreness_rule.py."""

import pytest

from app.domain.readiness.value_objects import SorenessLevel
from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity
from app.domain.safety.rules.soreness_rule import SorenessRule
from tests.domain.safety.rules.factories import a_readiness_context, a_safety_context

# --- identity ---


@pytest.mark.unit
def test_default_identity() -> None:
    rule = SorenessRule()
    assert rule.id == RuleId("safety.soreness")
    assert rule.name == "Soreness Safety"
    assert rule.severity == RecommendationSeverity.CRITICAL


# --- missing data ---


@pytest.mark.unit
def test_passes_when_no_readiness_supplied() -> None:
    rule = SorenessRule()
    result = rule.evaluate(a_safety_context())
    assert result.passed is True
    assert "No readiness check-in supplied" in result.explanation


@pytest.mark.unit
def test_passes_when_soreness_not_recorded() -> None:
    rule = SorenessRule()
    context = a_safety_context(readiness=a_readiness_context())
    result = rule.evaluate(context)
    assert result.passed is True
    assert "No soreness level recorded" in result.explanation


# --- thresholds ---


@pytest.mark.unit
def test_fails_at_or_above_the_critical_threshold() -> None:
    rule = SorenessRule(critical_soreness=9)
    context = a_safety_context(readiness=a_readiness_context(soreness_level=SorenessLevel(9)))
    result = rule.evaluate(context)
    assert result.passed is False
    assert result.triggered_rules == (RuleId("safety.soreness"),)
    assert len(result.recommendations) == 1


@pytest.mark.unit
def test_passes_below_the_critical_threshold() -> None:
    rule = SorenessRule(critical_soreness=9)
    context = a_safety_context(readiness=a_readiness_context(soreness_level=SorenessLevel(7)))
    result = rule.evaluate(context)
    assert result.passed is True


# --- determinism ---


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    rule = SorenessRule()
    context = a_safety_context(readiness=a_readiness_context(soreness_level=SorenessLevel(9)))
    assert rule.evaluate(context) == rule.evaluate(context)
