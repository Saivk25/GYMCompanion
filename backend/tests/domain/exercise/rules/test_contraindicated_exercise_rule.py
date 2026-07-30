"""Tests for app/domain/exercise/rules/contraindicated_exercise_rule.py."""

import pytest

from app.domain.exercise.rules.contraindicated_exercise_rule import ContraindicatedExerciseRule
from app.domain.exercise.value_objects import Contraindications
from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity
from tests.domain.exercise.rules.factories import (
    DeclaredRestriction,
    a_recommendation_context,
    a_rule_result,
    an_exercise_context,
)

# --- identity ---


@pytest.mark.unit
def test_default_identity() -> None:
    rule = ContraindicatedExerciseRule()
    assert rule.id == RuleId("exercise_recommendation.contraindicated_exercise")
    assert rule.name == "Contraindicated Exercise"
    assert rule.severity == RecommendationSeverity.WARNING


# --- no restriction data ---


@pytest.mark.unit
def test_passes_with_no_declared_restrictions_and_no_safety_result() -> None:
    rule = ContraindicatedExerciseRule()
    result = rule.evaluate(a_recommendation_context())
    assert result.passed is True
    assert "No declared restrictions" in result.explanation


# --- tag matching ---


@pytest.mark.unit
def test_passes_when_no_tags_overlap() -> None:
    rule = ContraindicatedExerciseRule()
    exercise = an_exercise_context(contraindications=Contraindications(frozenset({"knee_pain"})))
    context = a_recommendation_context(
        exercise=exercise, declared_restrictions=(DeclaredRestriction(tag="shoulder_pain"),)
    )
    result = rule.evaluate(context)
    assert result.passed is True


@pytest.mark.unit
def test_fails_when_a_tag_overlaps() -> None:
    rule = ContraindicatedExerciseRule()
    exercise = an_exercise_context(
        contraindications=Contraindications(frozenset({"shoulder_pain"}))
    )
    context = a_recommendation_context(
        exercise=exercise, declared_restrictions=(DeclaredRestriction(tag="shoulder_pain"),)
    )
    result = rule.evaluate(context)
    assert result.passed is False
    assert result.triggered_rules == (RuleId("exercise_recommendation.contraindicated_exercise"),)
    assert "shoulder_pain" in result.explanation
    assert len(result.recommendations) == 1


# --- safety_result override ---


@pytest.mark.unit
def test_fails_when_safety_result_is_critical_regardless_of_tags() -> None:
    rule = ContraindicatedExerciseRule()
    safety_result = a_rule_result(passed=False, severity=RecommendationSeverity.CRITICAL)
    context = a_recommendation_context(safety_result=safety_result)
    result = rule.evaluate(context)
    assert result.passed is False
    assert "CRITICAL" in result.explanation


@pytest.mark.unit
def test_passes_when_safety_result_is_not_critical() -> None:
    rule = ContraindicatedExerciseRule()
    safety_result = a_rule_result(passed=False, severity=RecommendationSeverity.WARNING)
    context = a_recommendation_context(safety_result=safety_result)
    result = rule.evaluate(context)
    assert result.passed is True


# --- determinism ---


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    rule = ContraindicatedExerciseRule()
    exercise = an_exercise_context(
        contraindications=Contraindications(frozenset({"shoulder_pain"}))
    )
    context = a_recommendation_context(
        exercise=exercise, declared_restrictions=(DeclaredRestriction(tag="shoulder_pain"),)
    )
    assert rule.evaluate(context) == rule.evaluate(context)
