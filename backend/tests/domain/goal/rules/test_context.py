"""Tests for app/domain/goal/rules/context.py."""

from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from app.domain.goal.context import GoalContext
from app.domain.goal.rules.context import GoalAlignmentRuleContext
from app.domain.progress.context import ProgressContext
from app.domain.progress.value_objects import BodyWeight
from app.domain.rules.context import RuleContext
from tests.domain.goal.factories import a_created_goal
from tests.domain.goal.factories import a_fixed_clock as a_goal_fixed_clock
from tests.domain.goal.rules.factories import a_goal_context, a_progress_context
from tests.domain.progress.factories import a_recorded_progress


@pytest.mark.unit
def test_is_a_rule_context() -> None:
    context = GoalAlignmentRuleContext(goal=a_goal_context(), reference_date=date(2026, 1, 1))
    assert isinstance(context, RuleContext)


@pytest.mark.unit
def test_progress_defaults_to_none() -> None:
    context = GoalAlignmentRuleContext(goal=a_goal_context(), reference_date=date(2026, 1, 1))
    assert context.progress is None


@pytest.mark.unit
def test_is_immutable() -> None:
    context = GoalAlignmentRuleContext(goal=a_goal_context(), reference_date=date(2026, 1, 1))
    with pytest.raises(FrozenInstanceError):
        context.reference_date = date(2026, 2, 1)  # type: ignore[misc]


# --- from_snapshots() ---


@pytest.mark.unit
def test_from_snapshots_builds_directly_from_the_given_snapshots() -> None:
    goal = a_goal_context()
    progress = a_progress_context(body_weight=BodyWeight(80.0))

    context = GoalAlignmentRuleContext.from_snapshots(
        goal=goal, progress=progress, reference_date=date(2026, 3, 1)
    )

    assert context.goal == goal
    assert context.progress == progress
    assert context.reference_date == date(2026, 3, 1)


@pytest.mark.unit
def test_from_snapshots_defaults_progress_to_none() -> None:
    goal = a_goal_context()
    context = GoalAlignmentRuleContext.from_snapshots(goal=goal, reference_date=date(2026, 3, 1))
    assert context.progress is None


# --- from_aggregates() ---


@pytest.mark.unit
def test_from_aggregates_snapshots_the_given_goal() -> None:
    goal = a_created_goal()
    clock = a_goal_fixed_clock()

    context = GoalAlignmentRuleContext.from_aggregates(goal=goal, progress=None, clock=clock)

    assert context.goal == GoalContext.from_goal(goal)
    assert context.progress is None


@pytest.mark.unit
def test_from_aggregates_snapshots_the_given_progress() -> None:
    goal = a_created_goal()
    progress = a_recorded_progress()
    clock = a_goal_fixed_clock()

    context = GoalAlignmentRuleContext.from_aggregates(goal=goal, progress=progress, clock=clock)

    assert context.progress == ProgressContext.from_progress(progress)


@pytest.mark.unit
def test_from_aggregates_stamps_reference_date_from_the_clock() -> None:
    goal = a_created_goal()
    clock = a_goal_fixed_clock()

    context = GoalAlignmentRuleContext.from_aggregates(goal=goal, progress=None, clock=clock)

    assert context.reference_date == clock.now().date()


@pytest.mark.unit
def test_from_aggregates_does_not_reflect_later_mutations_of_the_source_goal() -> None:
    from app.domain.goal.value_objects import GoalName

    goal = a_created_goal()
    clock = a_goal_fixed_clock()
    context = GoalAlignmentRuleContext.from_aggregates(goal=goal, progress=None, clock=clock)

    goal.update(name=GoalName("Renamed"), clock=clock)

    assert context.goal.name == GoalName("Lose 5kg")
    assert goal.name == GoalName("Renamed")
