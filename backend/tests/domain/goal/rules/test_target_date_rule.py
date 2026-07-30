"""Tests for app/domain/goal/rules/target_date_rule.py."""

from datetime import date

import pytest

from app.domain.goal.enums import GoalStatus
from app.domain.goal.rules.target_date_rule import TargetDateRule
from app.domain.goal.value_objects import TargetDate
from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity
from tests.domain.goal.rules.factories import a_goal_alignment_context, a_goal_context


@pytest.mark.unit
def test_exposes_id_name_description_severity() -> None:
    rule = TargetDateRule()
    assert rule.id == RuleId("goal_alignment.target_date")
    assert rule.name == "Target Date"
    assert rule.description
    assert rule.severity == RecommendationSeverity.WARNING


@pytest.mark.unit
def test_passes_for_a_non_active_goal() -> None:
    goal = a_goal_context(status=GoalStatus.COMPLETED, target_date=TargetDate(date(2026, 1, 1)))
    context = a_goal_alignment_context(goal=goal, reference_date=date(2026, 3, 1))
    result = TargetDateRule().evaluate(context)
    assert result.passed is True


@pytest.mark.unit
def test_passes_when_target_date_is_comfortably_in_the_future() -> None:
    goal = a_goal_context(target_date=TargetDate(date(2026, 6, 1)))
    context = a_goal_alignment_context(goal=goal, reference_date=date(2026, 1, 1))
    result = TargetDateRule().evaluate(context)
    assert result.passed is True


@pytest.mark.unit
def test_fails_when_target_date_is_within_the_approaching_window() -> None:
    goal = a_goal_context(target_date=TargetDate(date(2026, 1, 10)))
    context = a_goal_alignment_context(goal=goal, reference_date=date(2026, 1, 1))
    rule = TargetDateRule(approaching_within_days=14)
    result = rule.evaluate(context)
    assert result.passed is False
    assert result.triggered_rules == (rule.id,)
    assert len(result.recommendations) == 1


@pytest.mark.unit
def test_passes_at_exactly_beyond_the_approaching_window() -> None:
    goal = a_goal_context(target_date=TargetDate(date(2026, 1, 16)))
    context = a_goal_alignment_context(goal=goal, reference_date=date(2026, 1, 1))
    rule = TargetDateRule(approaching_within_days=14)
    result = rule.evaluate(context)
    assert result.passed is True


@pytest.mark.unit
def test_fails_at_exactly_the_approaching_boundary() -> None:
    goal = a_goal_context(target_date=TargetDate(date(2026, 1, 15)))
    context = a_goal_alignment_context(goal=goal, reference_date=date(2026, 1, 1))
    rule = TargetDateRule(approaching_within_days=14)
    result = rule.evaluate(context)
    assert result.passed is False


@pytest.mark.unit
def test_fails_when_target_date_has_passed() -> None:
    goal = a_goal_context(target_date=TargetDate(date(2025, 12, 1)))
    context = a_goal_alignment_context(goal=goal, reference_date=date(2026, 1, 1))
    rule = TargetDateRule()
    result = rule.evaluate(context)
    assert result.passed is False
    assert "overdue" in result.explanation


@pytest.mark.unit
def test_approaching_window_is_configurable() -> None:
    goal = a_goal_context(target_date=TargetDate(date(2026, 1, 10)))
    context = a_goal_alignment_context(goal=goal, reference_date=date(2026, 1, 1))
    assert TargetDateRule(approaching_within_days=3).evaluate(context).passed is True
    assert TargetDateRule(approaching_within_days=30).evaluate(context).passed is False


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    goal = a_goal_context(target_date=TargetDate(date(2025, 12, 1)))
    context = a_goal_alignment_context(goal=goal, reference_date=date(2026, 1, 1))
    rule = TargetDateRule()
    assert rule.evaluate(context) == rule.evaluate(context)
