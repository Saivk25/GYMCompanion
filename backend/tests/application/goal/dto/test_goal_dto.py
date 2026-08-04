"""Tests for app/application/goal/dto/goal_dto.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.application.goal.dto.goal_dto import GoalDTO
from app.domain.goal.enums import GoalStatus
from app.domain.goal.value_objects import GoalName
from tests.application.goal.factories import a_created_goal, a_fixed_clock


@pytest.mark.unit
def test_from_goal_maps_every_field_for_a_freshly_created_goal() -> None:
    goal = a_created_goal()

    dto = GoalDTO.from_goal(goal)

    assert dto.goal_id == goal.id
    assert dto.user_id == goal.user_id
    assert dto.goal_type == goal.goal_type
    assert dto.name == goal.name
    assert dto.target_date == goal.target_date
    assert dto.created_at == goal.created_at
    assert dto.description is None
    assert dto.target_weight is None
    assert dto.target_body_fat is None
    assert dto.target_strength is None
    assert dto.priority is None
    assert dto.notes == goal.notes
    assert dto.status == GoalStatus.ACTIVE
    assert dto.updated_at is None
    assert dto.completed_at is None
    assert dto.cancelled_at is None


@pytest.mark.unit
def test_from_goal_reflects_an_update() -> None:
    goal = a_created_goal()
    goal.update(name=GoalName("New Name"), clock=a_fixed_clock())

    dto = GoalDTO.from_goal(goal)

    assert dto.name == GoalName("New Name")
    assert dto.updated_at is not None


@pytest.mark.unit
def test_from_goal_reflects_completion() -> None:
    goal = a_created_goal()
    goal.complete(clock=a_fixed_clock())

    dto = GoalDTO.from_goal(goal)

    assert dto.status == GoalStatus.COMPLETED
    assert dto.completed_at is not None
    assert dto.cancelled_at is None


@pytest.mark.unit
def test_from_goal_reflects_cancellation() -> None:
    goal = a_created_goal()
    goal.cancel(clock=a_fixed_clock())

    dto = GoalDTO.from_goal(goal)

    assert dto.status == GoalStatus.CANCELLED
    assert dto.cancelled_at is not None
    assert dto.completed_at is None


@pytest.mark.unit
def test_goal_dto_is_immutable() -> None:
    dto = GoalDTO.from_goal(a_created_goal())
    with pytest.raises(FrozenInstanceError):
        dto.name = GoalName("Another Name")  # type: ignore[misc]
