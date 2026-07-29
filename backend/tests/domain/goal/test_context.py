"""Tests for app/domain/goal/context.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.domain.goal.context import GoalContext
from app.domain.goal.value_objects import GoalName, GoalNotes
from tests.domain.goal.factories import a_created_goal, a_fixed_clock


@pytest.mark.unit
def test_from_goal_snapshots_every_relevant_field() -> None:
    goal = a_created_goal()

    context = GoalContext.from_goal(goal)

    assert context.goal_id == goal.id
    assert context.user_id == goal.user_id
    assert context.goal_type == goal.goal_type
    assert context.name == goal.name
    assert context.target_date == goal.target_date
    assert context.status == goal.status
    assert context.description is None
    assert context.target_weight is None
    assert context.target_body_fat is None
    assert context.target_strength is None
    assert context.priority is None
    assert context.notes == GoalNotes()


@pytest.mark.unit
def test_is_immutable() -> None:
    goal = a_created_goal()
    context = GoalContext.from_goal(goal)
    with pytest.raises(FrozenInstanceError):
        context.notes = GoalNotes("changed")  # type: ignore[misc]


@pytest.mark.unit
def test_does_not_reflect_later_mutations_of_the_source_goal() -> None:
    goal = a_created_goal()
    context = GoalContext.from_goal(goal)

    goal.update(name=GoalName("Renamed"), clock=a_fixed_clock())

    assert context.name == GoalName("Lose 5kg")
    assert goal.name == GoalName("Renamed")
