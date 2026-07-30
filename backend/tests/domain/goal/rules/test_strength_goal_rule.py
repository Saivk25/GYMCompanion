"""Tests for app/domain/goal/rules/strength_goal_rule.py."""

import pytest

from app.domain.goal.enums import GoalStatus
from app.domain.goal.rules.strength_goal_rule import StrengthGoalRule
from app.domain.goal.value_objects import TargetStrength
from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity
from tests.domain.goal.rules.factories import a_goal_alignment_context, a_goal_context


@pytest.mark.unit
def test_exposes_id_name_description_severity() -> None:
    rule = StrengthGoalRule()
    assert rule.id == RuleId("goal_alignment.strength_goal")
    assert rule.name == "Strength Goal"
    assert rule.description
    assert rule.severity == RecommendationSeverity.INFO


@pytest.mark.unit
def test_always_passes_for_a_non_active_goal() -> None:
    goal = a_goal_context(status=GoalStatus.EXPIRED, target_strength=TargetStrength(100.0))
    context = a_goal_alignment_context(goal=goal)
    result = StrengthGoalRule().evaluate(context)
    assert result.passed is True


@pytest.mark.unit
def test_always_passes_with_no_strength_target() -> None:
    goal = a_goal_context(target_strength=None)
    context = a_goal_alignment_context(goal=goal)
    result = StrengthGoalRule().evaluate(context)
    assert result.passed is True
    assert "no strength target" in result.explanation.lower()


@pytest.mark.unit
def test_always_passes_with_a_strength_target_but_no_progress_data() -> None:
    goal = a_goal_context(target_strength=TargetStrength(100.0))
    context = a_goal_alignment_context(goal=goal)
    result = StrengthGoalRule().evaluate(context)
    assert result.passed is True
    assert "insufficient" in result.explanation.lower() or "no strength progress" in (
        result.explanation.lower()
    )


@pytest.mark.unit
def test_never_triggers_regardless_of_context() -> None:
    """Rule never fails — matches the task's explicit instruction that
    insufficient strength data always yields a passing result."""
    goal = a_goal_context(target_strength=TargetStrength(100.0))
    context = a_goal_alignment_context(goal=goal)
    result = StrengthGoalRule().evaluate(context)
    assert result.triggered_rules == ()
    assert result.recommendations == ()


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    goal = a_goal_context(target_strength=TargetStrength(100.0))
    context = a_goal_alignment_context(goal=goal)
    rule = StrengthGoalRule()
    assert rule.evaluate(context) == rule.evaluate(context)
