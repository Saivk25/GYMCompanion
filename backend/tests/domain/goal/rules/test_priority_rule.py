"""Tests for app/domain/goal/rules/priority_rule.py."""

import pytest

from app.domain.goal.enums import GoalStatus
from app.domain.goal.rules.priority_rule import PriorityRule
from app.domain.goal.value_objects import Priority
from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity
from tests.domain.goal.rules.factories import a_goal_alignment_context, a_goal_context


@pytest.mark.unit
def test_exposes_id_name_description_severity() -> None:
    rule = PriorityRule()
    assert rule.id == RuleId("goal_alignment.priority")
    assert rule.name == "Priority"
    assert rule.description
    assert rule.severity == RecommendationSeverity.ADVISORY


@pytest.mark.unit
def test_passes_for_a_non_active_goal() -> None:
    goal = a_goal_context(status=GoalStatus.COMPLETED, priority=Priority(1))
    context = a_goal_alignment_context(goal=goal)
    assert PriorityRule().evaluate(context).passed is True


@pytest.mark.unit
def test_passes_when_no_priority_is_set() -> None:
    goal = a_goal_context(priority=None)
    context = a_goal_alignment_context(goal=goal)
    assert PriorityRule().evaluate(context).passed is True


@pytest.mark.unit
def test_fails_for_a_high_priority_active_goal() -> None:
    goal = a_goal_context(priority=Priority(1))
    context = a_goal_alignment_context(goal=goal)
    rule = PriorityRule()
    result = rule.evaluate(context)
    assert result.passed is False
    assert result.triggered_rules == (rule.id,)
    assert len(result.recommendations) == 1


@pytest.mark.unit
def test_passes_for_a_low_priority_active_goal() -> None:
    goal = a_goal_context(priority=Priority(5))
    context = a_goal_alignment_context(goal=goal)
    assert PriorityRule().evaluate(context).passed is True


@pytest.mark.unit
def test_threshold_is_configurable() -> None:
    goal = a_goal_context(priority=Priority(3))
    context = a_goal_alignment_context(goal=goal)
    assert PriorityRule(maximum_priority_to_highlight=2).evaluate(context).passed is True
    assert PriorityRule(maximum_priority_to_highlight=4).evaluate(context).passed is False


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    goal = a_goal_context(priority=Priority(1))
    context = a_goal_alignment_context(goal=goal)
    rule = PriorityRule()
    assert rule.evaluate(context) == rule.evaluate(context)
