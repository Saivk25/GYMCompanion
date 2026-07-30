"""Tests for app/domain/exercise/rules/movement_balance_rule.py."""

import pytest

from app.domain.exercise.enums import MovementPattern
from app.domain.exercise.rules.movement_balance_rule import MovementBalanceRule
from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity
from tests.domain.exercise.rules.factories import a_recommendation_context, an_exercise_context

# --- identity ---


@pytest.mark.unit
def test_default_identity() -> None:
    rule = MovementBalanceRule()
    assert rule.id == RuleId("exercise_recommendation.movement_balance")
    assert rule.name == "Movement Balance"
    assert rule.severity == RecommendationSeverity.ADVISORY


# --- never fails / insufficient data ---


@pytest.mark.unit
def test_passes_with_no_recent_patterns() -> None:
    rule = MovementBalanceRule(minimum_entries=4)
    result = rule.evaluate(a_recommendation_context())
    assert result.passed is True
    assert "at least" in result.explanation


@pytest.mark.unit
def test_passes_when_neither_push_nor_pull_appear() -> None:
    rule = MovementBalanceRule(minimum_entries=2)
    patterns = (MovementPattern.SQUAT, MovementPattern.HINGE, MovementPattern.CORE)
    context = a_recommendation_context(recent_movement_patterns=patterns)
    result = rule.evaluate(context)
    assert result.passed is True
    assert "No push or pull" in result.explanation


@pytest.mark.unit
def test_passes_when_candidate_is_neither_push_nor_pull() -> None:
    rule = MovementBalanceRule(minimum_entries=2)
    patterns = (MovementPattern.PUSH, MovementPattern.PUSH, MovementPattern.PUSH)
    exercise = an_exercise_context(movement_pattern=MovementPattern.SQUAT)
    context = a_recommendation_context(exercise=exercise, recent_movement_patterns=patterns)
    result = rule.evaluate(context)
    assert result.passed is True
    assert "does not apply" in result.explanation


# --- imbalance bias ---


@pytest.mark.unit
def test_biases_away_from_the_over_represented_pattern() -> None:
    rule = MovementBalanceRule(minimum_entries=4, imbalance_ratio=1.5)
    patterns = (MovementPattern.PUSH,) * 6 + (MovementPattern.PULL,) * 1
    exercise = an_exercise_context(movement_pattern=MovementPattern.PUSH)
    context = a_recommendation_context(exercise=exercise, recent_movement_patterns=patterns)
    result = rule.evaluate(context)
    assert result.passed is True
    assert len(result.recommendations) == 1
    assert "pull" in result.recommendations[0].message.lower()


@pytest.mark.unit
def test_positively_frames_the_under_represented_pattern() -> None:
    rule = MovementBalanceRule(minimum_entries=4, imbalance_ratio=1.5)
    patterns = (MovementPattern.PUSH,) * 6 + (MovementPattern.PULL,) * 1
    exercise = an_exercise_context(movement_pattern=MovementPattern.PULL)
    context = a_recommendation_context(exercise=exercise, recent_movement_patterns=patterns)
    result = rule.evaluate(context)
    assert result.passed is True
    assert len(result.recommendations) == 1
    assert "balance" in result.recommendations[0].message.lower()


@pytest.mark.unit
def test_biases_away_from_pull_when_pull_is_over_represented() -> None:
    rule = MovementBalanceRule(minimum_entries=4, imbalance_ratio=1.5)
    patterns = (MovementPattern.PULL,) * 6 + (MovementPattern.PUSH,) * 1
    exercise = an_exercise_context(movement_pattern=MovementPattern.PULL)
    context = a_recommendation_context(exercise=exercise, recent_movement_patterns=patterns)
    result = rule.evaluate(context)
    assert result.passed is True
    assert len(result.recommendations) == 1
    assert "push" in result.recommendations[0].message.lower()


@pytest.mark.unit
def test_passes_with_no_recommendation_when_balanced() -> None:
    rule = MovementBalanceRule(minimum_entries=4, imbalance_ratio=1.5)
    patterns = (MovementPattern.PUSH,) * 3 + (MovementPattern.PULL,) * 3
    exercise = an_exercise_context(movement_pattern=MovementPattern.PUSH)
    context = a_recommendation_context(exercise=exercise, recent_movement_patterns=patterns)
    result = rule.evaluate(context)
    assert result.passed is True
    assert result.recommendations == ()


# --- determinism ---


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    rule = MovementBalanceRule(minimum_entries=4, imbalance_ratio=1.5)
    patterns = (MovementPattern.PUSH,) * 6 + (MovementPattern.PULL,) * 1
    exercise = an_exercise_context(movement_pattern=MovementPattern.PUSH)
    context = a_recommendation_context(exercise=exercise, recent_movement_patterns=patterns)
    assert rule.evaluate(context) == rule.evaluate(context)
