"""Tests for app/domain/progress/rules/body_fat_rule.py."""

from datetime import date

import pytest

from app.domain.goal.enums import GoalStatus
from app.domain.goal.value_objects import TargetBodyFat
from app.domain.progress.rules.body_fat_rule import BodyFatRule
from app.domain.progress.value_objects import BodyFatPercentage, ProgressDate
from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity
from tests.domain.progress.rules.factories import (
    a_goal_context,
    a_progress_context,
    a_progress_evaluation_context,
)

# --- identity ---


@pytest.mark.unit
def test_default_identity() -> None:
    rule = BodyFatRule()
    assert rule.id == RuleId("progress_evaluation.body_fat")
    assert rule.name == "Body Fat Trend"
    assert rule.severity == RecommendationSeverity.WARNING


# --- missing data ---


@pytest.mark.unit
def test_passes_when_no_goal_supplied() -> None:
    rule = BodyFatRule()
    result = rule.evaluate(a_progress_evaluation_context())
    assert result.passed is True
    assert "No active goal supplied" in result.explanation


@pytest.mark.unit
def test_passes_when_goal_is_not_active() -> None:
    rule = BodyFatRule()
    goal = a_goal_context(status=GoalStatus.CANCELLED)
    context = a_progress_evaluation_context(goal=goal)
    result = rule.evaluate(context)
    assert result.passed is True
    assert "not active" in result.explanation


@pytest.mark.unit
def test_passes_when_goal_has_no_target_body_fat() -> None:
    rule = BodyFatRule()
    goal = a_goal_context(target_body_fat=None)
    context = a_progress_evaluation_context(goal=goal)
    result = rule.evaluate(context)
    assert result.passed is True
    assert "no target body fat" in result.explanation


@pytest.mark.unit
def test_passes_when_fewer_than_minimum_entries() -> None:
    rule = BodyFatRule(minimum_entries=2)
    goal = a_goal_context(target_body_fat=TargetBodyFat(15.0))
    context = a_progress_evaluation_context(
        goal=goal,
        progress_history=[a_progress_context(body_fat_percentage=BodyFatPercentage(25.0))],
    )
    result = rule.evaluate(context)
    assert result.passed is True
    assert "at least 2" in result.explanation


# --- trend evaluation ---


@pytest.mark.unit
def test_passes_when_within_tolerance() -> None:
    rule = BodyFatRule(body_fat_tolerance=3.0)
    goal = a_goal_context(target_body_fat=TargetBodyFat(15.0))
    context = a_progress_evaluation_context(
        goal=goal,
        progress_history=[
            a_progress_context(
                progress_date=ProgressDate(date(2026, 1, 1)),
                body_fat_percentage=BodyFatPercentage(20.0),
            ),
            a_progress_context(
                progress_date=ProgressDate(date(2026, 1, 15)),
                body_fat_percentage=BodyFatPercentage(16.0),
            ),
        ],
    )
    result = rule.evaluate(context)
    assert result.passed is True
    assert "within" in result.explanation


@pytest.mark.unit
def test_passes_when_gap_narrows() -> None:
    rule = BodyFatRule(body_fat_tolerance=3.0)
    goal = a_goal_context(target_body_fat=TargetBodyFat(15.0))
    context = a_progress_evaluation_context(
        goal=goal,
        progress_history=[
            a_progress_context(
                progress_date=ProgressDate(date(2026, 1, 1)),
                body_fat_percentage=BodyFatPercentage(25.0),
            ),
            a_progress_context(
                progress_date=ProgressDate(date(2026, 1, 15)),
                body_fat_percentage=BodyFatPercentage(22.0),
            ),
        ],
    )
    result = rule.evaluate(context)
    assert result.passed is True
    assert "narrowed" in result.explanation


@pytest.mark.unit
def test_fails_when_gap_does_not_narrow() -> None:
    rule = BodyFatRule(body_fat_tolerance=3.0)
    goal = a_goal_context(target_body_fat=TargetBodyFat(15.0))
    context = a_progress_evaluation_context(
        goal=goal,
        progress_history=[
            a_progress_context(
                progress_date=ProgressDate(date(2026, 1, 1)),
                body_fat_percentage=BodyFatPercentage(20.0),
            ),
            a_progress_context(
                progress_date=ProgressDate(date(2026, 1, 15)),
                body_fat_percentage=BodyFatPercentage(24.0),
            ),
        ],
    )
    result = rule.evaluate(context)
    assert result.passed is False
    assert result.triggered_rules == (RuleId("progress_evaluation.body_fat"),)
    assert len(result.recommendations) == 1


# --- determinism ---


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    rule = BodyFatRule()
    goal = a_goal_context(target_body_fat=TargetBodyFat(15.0))
    context = a_progress_evaluation_context(
        goal=goal,
        progress_history=[
            a_progress_context(body_fat_percentage=BodyFatPercentage(20.0)),
            a_progress_context(body_fat_percentage=BodyFatPercentage(24.0)),
        ],
    )
    assert rule.evaluate(context) == rule.evaluate(context)
