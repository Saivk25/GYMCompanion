"""Tests for app/domain/safety/rules/contraindication_rule.py."""

import pytest

from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity
from app.domain.safety.rules.contraindication_rule import ContraindicationRule
from tests.domain.safety.rules.factories import a_declared_restriction, a_safety_context

# --- identity ---


@pytest.mark.unit
def test_default_identity() -> None:
    rule = ContraindicationRule()
    assert rule.id == RuleId("safety.contraindication")
    assert rule.name == "Contraindication"
    assert rule.severity == RecommendationSeverity.ADVISORY


# --- no restrictions ---


@pytest.mark.unit
def test_passes_when_no_restrictions_declared() -> None:
    rule = ContraindicationRule()
    result = rule.evaluate(a_safety_context())
    assert result.passed is True
    assert "No declared movement restrictions" in result.explanation


# --- restrictions declared ---


@pytest.mark.unit
def test_triggers_when_a_restriction_is_declared() -> None:
    rule = ContraindicationRule()
    restriction = a_declared_restriction(tag="overhead_pressing")
    context = a_safety_context(declared_restrictions=(restriction,))
    result = rule.evaluate(context)
    assert result.passed is False
    assert result.triggered_rules == (RuleId("safety.contraindication"),)
    assert "overhead_pressing" in result.explanation
    assert len(result.recommendations) == 1
    assert "overhead_pressing" in result.recommendations[0].message


@pytest.mark.unit
def test_lists_multiple_restrictions() -> None:
    rule = ContraindicationRule()
    restrictions = (
        a_declared_restriction(tag="overhead_pressing"),
        a_declared_restriction(tag="deep_knee_flexion"),
    )
    context = a_safety_context(declared_restrictions=restrictions)
    result = rule.evaluate(context)
    assert result.passed is False
    assert "overhead_pressing" in result.explanation
    assert "deep_knee_flexion" in result.explanation


# --- determinism ---


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    rule = ContraindicationRule()
    context = a_safety_context(declared_restrictions=(a_declared_restriction(),))
    assert rule.evaluate(context) == rule.evaluate(context)
