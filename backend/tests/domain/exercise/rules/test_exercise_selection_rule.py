"""Tests for app/domain/exercise/rules/exercise_selection_rule.py."""

import pytest

from app.domain.exercise.enums import MovementPattern
from app.domain.exercise.rules.exercise_selection_rule import ExerciseSelectionRule
from app.domain.goal.enums import GoalStatus, GoalType
from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity
from tests.domain.exercise.rules.factories import (
    a_goal_context,
    a_recommendation_context,
    a_rule_result,
    an_exercise_context,
)

# --- identity ---


@pytest.mark.unit
def test_default_identity() -> None:
    rule = ExerciseSelectionRule()
    assert rule.id == RuleId("exercise_recommendation.exercise_selection")
    assert rule.name == "Exercise Selection"
    assert rule.severity == RecommendationSeverity.ADVISORY


# --- never fails ---


@pytest.mark.unit
def test_passes_with_no_goal_and_no_readiness_result() -> None:
    rule = ExerciseSelectionRule()
    context = a_recommendation_context()
    result = rule.evaluate(context)
    assert result.passed is True
    assert result.triggered_rules == ()
    assert result.recommendations == ()


@pytest.mark.unit
def test_passes_when_goal_is_not_active() -> None:
    rule = ExerciseSelectionRule()
    goal = a_goal_context(goal_type=GoalType.STRENGTH, status=GoalStatus.COMPLETED)
    exercise = an_exercise_context(movement_pattern=MovementPattern.CARDIO)
    context = a_recommendation_context(goal=goal, exercise=exercise)
    result = rule.evaluate(context)
    assert result.passed is True
    assert result.recommendations == ()


# --- goal-type bias ---


@pytest.mark.unit
def test_biases_away_from_cardio_for_a_strength_goal() -> None:
    rule = ExerciseSelectionRule()
    goal = a_goal_context(goal_type=GoalType.STRENGTH, status=GoalStatus.ACTIVE)
    exercise = an_exercise_context(movement_pattern=MovementPattern.CARDIO)
    context = a_recommendation_context(goal=goal, exercise=exercise)
    result = rule.evaluate(context)
    assert result.passed is True
    assert len(result.recommendations) == 1
    assert "strength" in result.recommendations[0].message.lower()


@pytest.mark.unit
def test_biases_toward_cardio_for_an_endurance_goal() -> None:
    rule = ExerciseSelectionRule()
    goal = a_goal_context(goal_type=GoalType.ENDURANCE, status=GoalStatus.ACTIVE)
    exercise = an_exercise_context(movement_pattern=MovementPattern.SQUAT)
    context = a_recommendation_context(goal=goal, exercise=exercise)
    result = rule.evaluate(context)
    assert result.passed is True
    assert len(result.recommendations) == 1
    assert "cardio" in result.recommendations[0].message.lower()


@pytest.mark.unit
def test_no_bias_for_an_endurance_goal_with_a_cardio_exercise() -> None:
    rule = ExerciseSelectionRule()
    goal = a_goal_context(goal_type=GoalType.ENDURANCE, status=GoalStatus.ACTIVE)
    exercise = an_exercise_context(movement_pattern=MovementPattern.CARDIO)
    context = a_recommendation_context(goal=goal, exercise=exercise)
    result = rule.evaluate(context)
    assert result.passed is True
    assert result.recommendations == ()


@pytest.mark.unit
def test_no_bias_for_a_goal_type_with_no_opinion() -> None:
    rule = ExerciseSelectionRule()
    goal = a_goal_context(goal_type=GoalType.GENERAL_HEALTH, status=GoalStatus.ACTIVE)
    exercise = an_exercise_context(movement_pattern=MovementPattern.CARDIO)
    context = a_recommendation_context(goal=goal, exercise=exercise)
    result = rule.evaluate(context)
    assert result.passed is True
    assert result.recommendations == ()


# --- readiness bias ---


@pytest.mark.unit
def test_biases_toward_easier_when_readiness_result_is_not_passing() -> None:
    rule = ExerciseSelectionRule()
    readiness_result = a_rule_result(passed=False)
    context = a_recommendation_context(readiness_result=readiness_result)
    result = rule.evaluate(context)
    assert result.passed is True
    assert len(result.recommendations) == 1
    assert "readiness" in result.recommendations[0].message.lower()


@pytest.mark.unit
def test_goal_bias_takes_priority_over_readiness_bias() -> None:
    rule = ExerciseSelectionRule()
    goal = a_goal_context(goal_type=GoalType.STRENGTH, status=GoalStatus.ACTIVE)
    exercise = an_exercise_context(movement_pattern=MovementPattern.CARDIO)
    readiness_result = a_rule_result(passed=False)
    context = a_recommendation_context(
        goal=goal, exercise=exercise, readiness_result=readiness_result
    )
    result = rule.evaluate(context)
    assert len(result.recommendations) == 1
    assert "strength" in result.recommendations[0].message.lower()


# --- determinism ---


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    rule = ExerciseSelectionRule()
    goal = a_goal_context(goal_type=GoalType.STRENGTH, status=GoalStatus.ACTIVE)
    exercise = an_exercise_context(movement_pattern=MovementPattern.CARDIO)
    context = a_recommendation_context(goal=goal, exercise=exercise)
    assert rule.evaluate(context) == rule.evaluate(context)
