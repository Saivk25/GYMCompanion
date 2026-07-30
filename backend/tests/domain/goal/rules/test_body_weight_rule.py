"""Tests for app/domain/goal/rules/body_weight_rule.py."""

import pytest

from app.domain.goal.enums import GoalStatus
from app.domain.goal.rules.body_weight_rule import BodyWeightRule
from app.domain.goal.value_objects import TargetWeight
from app.domain.progress.value_objects import BodyWeight
from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity
from tests.domain.goal.rules.factories import (
    a_goal_alignment_context,
    a_goal_context,
    a_progress_context,
)


@pytest.mark.unit
def test_exposes_id_name_description_severity() -> None:
    rule = BodyWeightRule()
    assert rule.id == RuleId("goal_alignment.body_weight")
    assert rule.name == "Body Weight"
    assert rule.description
    assert rule.severity == RecommendationSeverity.ADVISORY


@pytest.mark.unit
def test_passes_for_a_non_active_goal() -> None:
    goal = a_goal_context(status=GoalStatus.COMPLETED, target_weight=TargetWeight(70.0))
    progress = a_progress_context(body_weight=BodyWeight(90.0))
    context = a_goal_alignment_context(goal=goal, progress=progress)
    assert BodyWeightRule().evaluate(context).passed is True


@pytest.mark.unit
def test_passes_when_goal_has_no_target_weight() -> None:
    goal = a_goal_context(target_weight=None)
    progress = a_progress_context(body_weight=BodyWeight(90.0))
    context = a_goal_alignment_context(goal=goal, progress=progress)
    assert BodyWeightRule().evaluate(context).passed is True


@pytest.mark.unit
def test_passes_when_no_progress_snapshot_is_given() -> None:
    goal = a_goal_context(target_weight=TargetWeight(70.0))
    context = a_goal_alignment_context(goal=goal, progress=None)
    assert BodyWeightRule().evaluate(context).passed is True


@pytest.mark.unit
def test_passes_when_progress_has_no_body_weight() -> None:
    goal = a_goal_context(target_weight=TargetWeight(70.0))
    progress = a_progress_context(body_weight=None)
    context = a_goal_alignment_context(goal=goal, progress=progress)
    assert BodyWeightRule().evaluate(context).passed is True


@pytest.mark.unit
def test_passes_within_tolerance() -> None:
    goal = a_goal_context(target_weight=TargetWeight(70.0))
    progress = a_progress_context(body_weight=BodyWeight(71.0))
    context = a_goal_alignment_context(goal=goal, progress=progress)
    result = BodyWeightRule(weight_tolerance=2.0).evaluate(context)
    assert result.passed is True


@pytest.mark.unit
def test_fails_outside_tolerance() -> None:
    goal = a_goal_context(target_weight=TargetWeight(70.0))
    progress = a_progress_context(body_weight=BodyWeight(80.0))
    context = a_goal_alignment_context(goal=goal, progress=progress)
    rule = BodyWeightRule(weight_tolerance=2.0)
    result = rule.evaluate(context)
    assert result.passed is False
    assert result.triggered_rules == (rule.id,)
    assert len(result.recommendations) == 1


@pytest.mark.unit
def test_tolerance_is_configurable() -> None:
    goal = a_goal_context(target_weight=TargetWeight(70.0))
    progress = a_progress_context(body_weight=BodyWeight(75.0))
    context = a_goal_alignment_context(goal=goal, progress=progress)
    assert BodyWeightRule(weight_tolerance=10.0).evaluate(context).passed is True
    assert BodyWeightRule(weight_tolerance=1.0).evaluate(context).passed is False


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    goal = a_goal_context(target_weight=TargetWeight(70.0))
    progress = a_progress_context(body_weight=BodyWeight(80.0))
    context = a_goal_alignment_context(goal=goal, progress=progress)
    rule = BodyWeightRule()
    assert rule.evaluate(context) == rule.evaluate(context)
