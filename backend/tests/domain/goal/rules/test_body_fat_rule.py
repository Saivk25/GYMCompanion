"""Tests for app/domain/goal/rules/body_fat_rule.py."""

import pytest

from app.domain.goal.enums import GoalStatus
from app.domain.goal.rules.body_fat_rule import BodyFatRule
from app.domain.goal.value_objects import TargetBodyFat
from app.domain.progress.value_objects import BodyFatPercentage
from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity
from tests.domain.goal.rules.factories import (
    a_goal_alignment_context,
    a_goal_context,
    a_progress_context,
)


@pytest.mark.unit
def test_exposes_id_name_description_severity() -> None:
    rule = BodyFatRule()
    assert rule.id == RuleId("goal_alignment.body_fat")
    assert rule.name == "Body Fat"
    assert rule.description
    assert rule.severity == RecommendationSeverity.ADVISORY


@pytest.mark.unit
def test_passes_for_a_non_active_goal() -> None:
    goal = a_goal_context(status=GoalStatus.CANCELLED, target_body_fat=TargetBodyFat(15.0))
    progress = a_progress_context(body_fat_percentage=BodyFatPercentage(25.0))
    context = a_goal_alignment_context(goal=goal, progress=progress)
    assert BodyFatRule().evaluate(context).passed is True


@pytest.mark.unit
def test_passes_when_goal_has_no_target_body_fat() -> None:
    goal = a_goal_context(target_body_fat=None)
    progress = a_progress_context(body_fat_percentage=BodyFatPercentage(25.0))
    context = a_goal_alignment_context(goal=goal, progress=progress)
    assert BodyFatRule().evaluate(context).passed is True


@pytest.mark.unit
def test_passes_when_no_progress_snapshot_is_given() -> None:
    goal = a_goal_context(target_body_fat=TargetBodyFat(15.0))
    context = a_goal_alignment_context(goal=goal, progress=None)
    assert BodyFatRule().evaluate(context).passed is True


@pytest.mark.unit
def test_passes_when_progress_has_no_body_fat_percentage() -> None:
    goal = a_goal_context(target_body_fat=TargetBodyFat(15.0))
    progress = a_progress_context(body_fat_percentage=None)
    context = a_goal_alignment_context(goal=goal, progress=progress)
    assert BodyFatRule().evaluate(context).passed is True


@pytest.mark.unit
def test_passes_within_tolerance() -> None:
    goal = a_goal_context(target_body_fat=TargetBodyFat(15.0))
    progress = a_progress_context(body_fat_percentage=BodyFatPercentage(17.0))
    context = a_goal_alignment_context(goal=goal, progress=progress)
    result = BodyFatRule(body_fat_tolerance=3.0).evaluate(context)
    assert result.passed is True


@pytest.mark.unit
def test_fails_outside_tolerance() -> None:
    goal = a_goal_context(target_body_fat=TargetBodyFat(15.0))
    progress = a_progress_context(body_fat_percentage=BodyFatPercentage(25.0))
    context = a_goal_alignment_context(goal=goal, progress=progress)
    rule = BodyFatRule(body_fat_tolerance=3.0)
    result = rule.evaluate(context)
    assert result.passed is False
    assert result.triggered_rules == (rule.id,)
    assert len(result.recommendations) == 1


@pytest.mark.unit
def test_tolerance_is_configurable() -> None:
    goal = a_goal_context(target_body_fat=TargetBodyFat(15.0))
    progress = a_progress_context(body_fat_percentage=BodyFatPercentage(20.0))
    context = a_goal_alignment_context(goal=goal, progress=progress)
    assert BodyFatRule(body_fat_tolerance=10.0).evaluate(context).passed is True
    assert BodyFatRule(body_fat_tolerance=1.0).evaluate(context).passed is False


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    goal = a_goal_context(target_body_fat=TargetBodyFat(15.0))
    progress = a_progress_context(body_fat_percentage=BodyFatPercentage(25.0))
    context = a_goal_alignment_context(goal=goal, progress=progress)
    rule = BodyFatRule()
    assert rule.evaluate(context) == rule.evaluate(context)
