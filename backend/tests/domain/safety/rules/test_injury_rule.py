"""Tests for app/domain/safety/rules/injury_rule.py."""

import pytest

from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity
from app.domain.safety.rules.injury_rule import InjuryRule
from tests.domain.safety.rules.factories import a_safety_context, an_active_injury

# --- identity ---


@pytest.mark.unit
def test_default_identity() -> None:
    rule = InjuryRule()
    assert rule.id == RuleId("safety.injury")
    assert rule.name == "Injury"
    assert rule.severity == RecommendationSeverity.CRITICAL


# --- no injuries ---


@pytest.mark.unit
def test_passes_when_no_injuries_declared() -> None:
    rule = InjuryRule()
    result = rule.evaluate(a_safety_context())
    assert result.passed is True
    assert "No active injuries" in result.explanation


# --- restricting injuries ---


@pytest.mark.unit
def test_triggers_when_an_injury_restricts_training() -> None:
    rule = InjuryRule()
    injury = an_active_injury(description="Left shoulder strain", restricts_training=True)
    context = a_safety_context(active_injuries=(injury,))
    result = rule.evaluate(context)
    assert result.passed is False
    assert result.triggered_rules == (RuleId("safety.injury"),)
    assert "Left shoulder strain" in result.explanation
    assert len(result.recommendations) == 1


@pytest.mark.unit
def test_lists_only_restricting_injuries_in_the_failure_explanation() -> None:
    rule = InjuryRule()
    restricting = an_active_injury(description="Left shoulder strain", restricts_training=True)
    cleared = an_active_injury(description="Old ankle sprain", restricts_training=False)
    context = a_safety_context(active_injuries=(restricting, cleared))
    result = rule.evaluate(context)
    assert result.passed is False
    assert "Left shoulder strain" in result.explanation
    assert "Old ankle sprain" not in result.explanation


# --- non-restricting injuries only ---


@pytest.mark.unit
def test_passes_when_no_injury_restricts_training() -> None:
    rule = InjuryRule()
    cleared = an_active_injury(description="Old ankle sprain", restricts_training=False)
    context = a_safety_context(active_injuries=(cleared,))
    result = rule.evaluate(context)
    assert result.passed is True
    assert "Old ankle sprain" in result.explanation


# --- determinism ---


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    rule = InjuryRule()
    context = a_safety_context(active_injuries=(an_active_injury(),))
    assert rule.evaluate(context) == rule.evaluate(context)
