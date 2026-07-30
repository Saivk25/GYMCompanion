"""Tests for app/domain/goal/rules/goal_alignment_rule_engine.py."""

from datetime import date

import pytest

from app.domain.goal.rules.body_fat_rule import BodyFatRule
from app.domain.goal.rules.body_weight_rule import BodyWeightRule
from app.domain.goal.rules.goal_alignment_rule_engine import GoalAlignmentRuleEngine
from app.domain.goal.rules.priority_rule import PriorityRule
from app.domain.goal.rules.strength_goal_rule import StrengthGoalRule
from app.domain.goal.rules.target_date_rule import TargetDateRule
from app.domain.goal.value_objects import Priority, TargetBodyFat, TargetDate, TargetWeight
from app.domain.progress.value_objects import BodyFatPercentage, BodyWeight
from app.domain.rules.engine import RuleEngine
from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity
from tests.domain.goal.rules.factories import (
    a_goal_alignment_context,
    a_goal_context,
    a_progress_context,
)


@pytest.mark.unit
def test_is_a_rule_engine() -> None:
    assert isinstance(GoalAlignmentRuleEngine(), RuleEngine)


@pytest.mark.unit
def test_default_construction_registers_all_five_rules() -> None:
    engine = GoalAlignmentRuleEngine()
    rule_types = {type(rule) for rule in engine.rules}
    expected_rule_types: set[type[object]] = {
        TargetDateRule,
        BodyWeightRule,
        BodyFatRule,
        StrengthGoalRule,
        PriorityRule,
    }
    assert rule_types == expected_rule_types
    assert len(engine.rules) == 5


@pytest.mark.unit
def test_accepts_a_custom_rule_set() -> None:
    custom_rule = TargetDateRule(rule_id=RuleId("custom.target_date"))
    engine = GoalAlignmentRuleEngine([custom_rule])
    assert engine.rules == (custom_rule,)


# --- evaluate(): a well-aligned active goal ---


@pytest.mark.unit
def test_evaluating_a_well_aligned_goal_passes() -> None:
    goal = a_goal_context(
        target_date=TargetDate(date(2026, 12, 1)),
        target_weight=TargetWeight(70.0),
        target_body_fat=TargetBodyFat(15.0),
        priority=Priority(5),
    )
    progress = a_progress_context(
        body_weight=BodyWeight(70.5),
        body_fat_percentage=BodyFatPercentage(16.0),
    )
    context = a_goal_alignment_context(
        goal=goal, progress=progress, reference_date=date(2026, 1, 1)
    )

    result = GoalAlignmentRuleEngine().evaluate(context)

    assert result.passed is True
    assert result.triggered_rules == ()


# --- evaluate(): a goal needing attention on every dimension ---


@pytest.mark.unit
def test_evaluating_a_goal_needing_attention_triggers_the_relevant_rules() -> None:
    goal = a_goal_context(
        target_date=TargetDate(date(2025, 12, 1)),  # overdue
        target_weight=TargetWeight(70.0),
        target_body_fat=TargetBodyFat(15.0),
        priority=Priority(1),  # high priority
    )
    progress = a_progress_context(
        body_weight=BodyWeight(90.0),  # far from target
        body_fat_percentage=BodyFatPercentage(30.0),  # far from target
    )
    context = a_goal_alignment_context(
        goal=goal, progress=progress, reference_date=date(2026, 1, 1)
    )

    result = GoalAlignmentRuleEngine().evaluate(context)

    assert result.passed is False
    assert set(result.triggered_rules) == {
        RuleId("goal_alignment.target_date"),
        RuleId("goal_alignment.body_weight"),
        RuleId("goal_alignment.body_fat"),
        RuleId("goal_alignment.priority"),
    }
    # StrengthGoalRule never triggers, by design.
    assert RuleId("goal_alignment.strength_goal") not in result.triggered_rules


@pytest.mark.unit
def test_evaluating_a_goal_with_no_progress_data_mostly_passes() -> None:
    goal = a_goal_context(
        target_date=TargetDate(date(2026, 12, 1)),
        target_weight=TargetWeight(70.0),
        target_body_fat=TargetBodyFat(15.0),
    )
    context = a_goal_alignment_context(goal=goal, progress=None, reference_date=date(2026, 1, 1))

    result = GoalAlignmentRuleEngine().evaluate(context)

    assert result.passed is True


@pytest.mark.unit
def test_evaluating_a_non_active_goal_passes_every_rule() -> None:
    from app.domain.goal.enums import GoalStatus

    goal = a_goal_context(
        status=GoalStatus.COMPLETED,
        target_date=TargetDate(date(2025, 1, 1)),
        priority=Priority(1),
    )
    context = a_goal_alignment_context(goal=goal, reference_date=date(2026, 1, 1))

    result = GoalAlignmentRuleEngine().evaluate(context)

    assert result.passed is True
    assert result.severity == RecommendationSeverity.INFO


# --- determinism / side-effect freedom ---


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    goal = a_goal_context(priority=Priority(1))
    context = a_goal_alignment_context(goal=goal)
    engine = GoalAlignmentRuleEngine()
    assert engine.evaluate(context) == engine.evaluate(context)


@pytest.mark.unit
def test_evaluate_does_not_mutate_the_context() -> None:
    goal = a_goal_context(priority=Priority(1))
    context = a_goal_alignment_context(goal=goal)
    GoalAlignmentRuleEngine().evaluate(context)
    assert context.goal.priority == Priority(1)
