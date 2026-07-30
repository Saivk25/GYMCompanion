"""Tests for app/domain/progress/rules/context.py."""

from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from app.domain.goal.enums import GoalType
from app.domain.goal.goal import Goal
from app.domain.goal.identifiers import GoalId
from app.domain.goal.value_objects import GoalName, Priority, TargetDate
from app.domain.progress.enums import MeasurementUnit, ProgressSource
from app.domain.progress.identifiers import ProgressId
from app.domain.progress.progress import Progress
from app.domain.progress.rules.context import ProgressEvaluationRuleContext
from app.domain.progress.value_objects import ProgressDate
from app.domain.rules.context import RuleContext
from app.domain.shared_kernel.clock import Clock
from app.domain.user.identifiers import UserId
from tests.domain.progress.rules.factories import (
    a_fixed_clock,
    a_goal_context,
    a_progress_context,
    a_progress_evaluation_context,
)

# --- construction ---


@pytest.mark.unit
def test_is_a_rule_context() -> None:
    context = ProgressEvaluationRuleContext(progress_history=(), reference_date=date(2026, 1, 1))
    assert isinstance(context, RuleContext)


@pytest.mark.unit
def test_defaults_goal_to_none() -> None:
    context = ProgressEvaluationRuleContext(progress_history=(), reference_date=date(2026, 1, 1))
    assert context.goal is None


@pytest.mark.unit
def test_is_immutable() -> None:
    context = a_progress_evaluation_context()
    with pytest.raises(FrozenInstanceError):
        context.goal = a_goal_context()  # type: ignore[misc]


# --- from_snapshots() ---


@pytest.mark.unit
def test_from_snapshots_sorts_chronologically() -> None:
    later_entry = a_progress_context(progress_date=ProgressDate(date(2026, 2, 1)))
    earlier_entry = a_progress_context(progress_date=ProgressDate(date(2026, 1, 1)))

    context = ProgressEvaluationRuleContext.from_snapshots(
        progress_history=[later_entry, earlier_entry], reference_date=date(2026, 3, 1)
    )

    assert [entry.progress_date.value for entry in context.progress_history] == [
        date(2026, 1, 1),
        date(2026, 2, 1),
    ]


@pytest.mark.unit
def test_from_snapshots_carries_goal_and_reference_date_through() -> None:
    goal = a_goal_context()
    context = ProgressEvaluationRuleContext.from_snapshots(
        progress_history=[], goal=goal, reference_date=date(2026, 5, 1)
    )
    assert context.goal == goal
    assert context.reference_date == date(2026, 5, 1)


@pytest.mark.unit
def test_from_snapshots_with_no_entries_is_empty() -> None:
    context = ProgressEvaluationRuleContext.from_snapshots(
        progress_history=[], reference_date=date(2026, 1, 1)
    )
    assert context.progress_history == ()


@pytest.mark.unit
def test_from_snapshots_does_not_reflect_a_later_mutated_list() -> None:
    entries = [a_progress_context(progress_date=ProgressDate(date(2026, 1, 1)))]
    context = ProgressEvaluationRuleContext.from_snapshots(
        progress_history=entries, reference_date=date(2026, 1, 1)
    )

    entries.append(a_progress_context(progress_date=ProgressDate(date(2026, 1, 2))))

    assert len(context.progress_history) == 1


# --- from_aggregates() ---


def _a_progress(*, user_id: UserId, clock: Clock) -> Progress:
    return Progress.record(
        progress_id=ProgressId.generate(),
        user_id=user_id,
        progress_date=ProgressDate(date(2026, 1, 1)),
        unit=MeasurementUnit.METRIC,
        source=ProgressSource.MANUAL,
        clock=clock,
    )


def _a_goal(*, user_id: UserId, clock: Clock) -> Goal:
    return Goal.create(
        goal_id=GoalId.generate(),
        user_id=user_id,
        goal_type=GoalType.LOSE_FAT,
        name=GoalName("Lose 5kg"),
        target_date=TargetDate(date(2026, 6, 1)),
        clock=clock,
    )


@pytest.mark.unit
def test_from_aggregates_builds_from_live_progress_and_goal() -> None:
    user_id = UserId.generate()
    clock = a_fixed_clock()
    progress = _a_progress(user_id=user_id, clock=clock)
    goal = _a_goal(user_id=user_id, clock=clock)

    context = ProgressEvaluationRuleContext.from_aggregates(
        progress_records=[progress], goal=goal, clock=clock
    )

    assert len(context.progress_history) == 1
    assert context.progress_history[0].progress_id == progress.id
    assert context.goal is not None
    assert context.goal.goal_id == goal.id
    assert context.reference_date == clock.now().date()


@pytest.mark.unit
def test_from_aggregates_with_no_goal() -> None:
    clock = a_fixed_clock()
    context = ProgressEvaluationRuleContext.from_aggregates(
        progress_records=[], goal=None, clock=clock
    )
    assert context.goal is None
    assert context.progress_history == ()


@pytest.mark.unit
def test_from_aggregates_does_not_reflect_later_mutations() -> None:
    clock = a_fixed_clock()
    goal = _a_goal(user_id=UserId.generate(), clock=clock)

    context = ProgressEvaluationRuleContext.from_aggregates(
        progress_records=[], goal=goal, clock=clock
    )

    goal.update(priority=Priority(1), clock=clock)

    assert context.goal is not None
    assert context.goal.priority is None
