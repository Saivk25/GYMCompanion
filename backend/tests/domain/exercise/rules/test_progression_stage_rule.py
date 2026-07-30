"""Tests for app/domain/exercise/rules/progression_stage_rule.py."""

import pytest

from app.domain.exercise.enums import Difficulty
from app.domain.exercise.rules.progression_stage_rule import ProgressionStageRule
from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity
from tests.domain.exercise.rules.factories import (
    a_progressive_overload_context,
    a_recommendation_context,
    a_summary,
    an_exercise_context,
)

# --- identity ---


@pytest.mark.unit
def test_default_identity() -> None:
    rule = ProgressionStageRule()
    assert rule.id == RuleId("exercise_recommendation.progression_stage")
    assert rule.name == "Progression Stage"
    assert rule.severity == RecommendationSeverity.ADVISORY


# --- beginner always appropriate ---


@pytest.mark.unit
def test_passes_for_beginner_difficulty_regardless_of_history() -> None:
    rule = ProgressionStageRule()
    exercise = an_exercise_context(difficulty=Difficulty.BEGINNER)
    context = a_recommendation_context(exercise=exercise)
    result = rule.evaluate(context)
    assert result.passed is True
    assert result.recommendations == ()


# --- missing data ---


@pytest.mark.unit
def test_passes_when_no_progressive_overload_context_supplied() -> None:
    rule = ProgressionStageRule()
    exercise = an_exercise_context(difficulty=Difficulty.ADVANCED)
    context = a_recommendation_context(exercise=exercise)
    result = rule.evaluate(context)
    assert result.passed is True
    assert "No training history" in result.explanation


# --- thin history bias ---


@pytest.mark.unit
def test_advises_caution_for_advanced_with_thin_history() -> None:
    rule = ProgressionStageRule(advanced_minimum_sessions=12)
    exercise = an_exercise_context(difficulty=Difficulty.ADVANCED)
    history = a_progressive_overload_context(sessions=[a_summary()] * 3)
    context = a_recommendation_context(exercise=exercise, progressive_overload=history)
    result = rule.evaluate(context)
    assert result.passed is True
    assert len(result.recommendations) == 1
    assert "advanced" in result.recommendations[0].message.lower()


@pytest.mark.unit
def test_advises_caution_for_intermediate_with_thin_history() -> None:
    rule = ProgressionStageRule(intermediate_minimum_sessions=4)
    exercise = an_exercise_context(difficulty=Difficulty.INTERMEDIATE)
    history = a_progressive_overload_context(sessions=[a_summary()] * 1)
    context = a_recommendation_context(exercise=exercise, progressive_overload=history)
    result = rule.evaluate(context)
    assert result.passed is True
    assert len(result.recommendations) == 1


@pytest.mark.unit
def test_no_recommendation_when_history_meets_the_minimum() -> None:
    rule = ProgressionStageRule(advanced_minimum_sessions=12)
    exercise = an_exercise_context(difficulty=Difficulty.ADVANCED)
    history = a_progressive_overload_context(sessions=[a_summary()] * 12)
    context = a_recommendation_context(exercise=exercise, progressive_overload=history)
    result = rule.evaluate(context)
    assert result.passed is True
    assert result.recommendations == ()


# --- determinism ---


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    rule = ProgressionStageRule(advanced_minimum_sessions=12)
    exercise = an_exercise_context(difficulty=Difficulty.ADVANCED)
    history = a_progressive_overload_context(sessions=[a_summary()] * 3)
    context = a_recommendation_context(exercise=exercise, progressive_overload=history)
    assert rule.evaluate(context) == rule.evaluate(context)
