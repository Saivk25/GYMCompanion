"""Tests for app/domain/goal/events.py.

Immutability, `event_id` auto-generation, and `occurred_at` timezone
enforcement are `DomainEvent` base behavior, already fully covered by
`tests/domain/shared_kernel/test_events.py`. This file only proves each
Goal-specific event carries the fields it's supposed to.
"""

from datetime import date, datetime, timezone

import pytest

from app.domain.goal.enums import GoalType
from app.domain.goal.events import GoalCancelled, GoalCompleted, GoalCreated, GoalUpdated
from app.domain.goal.identifiers import GoalId
from app.domain.goal.value_objects import GoalName, TargetDate
from app.domain.user.identifiers import UserId


@pytest.mark.unit
def test_goal_created_carries_the_identifying_fields() -> None:
    goal_id = GoalId.generate()
    user_id = UserId.generate()
    name = GoalName("Lose 5kg")
    target_date = TargetDate(date(2026, 6, 1))
    event = GoalCreated(
        occurred_at=datetime.now(timezone.utc),
        goal_id=goal_id,
        user_id=user_id,
        goal_type=GoalType.LOSE_FAT,
        name=name,
        target_date=target_date,
    )
    assert event.goal_id == goal_id
    assert event.user_id == user_id
    assert event.goal_type is GoalType.LOSE_FAT
    assert event.name == name
    assert event.target_date == target_date


@pytest.mark.unit
def test_goal_updated_carries_the_goal_id_and_name() -> None:
    goal_id = GoalId.generate()
    name = GoalName("Renamed goal")
    event = GoalUpdated(
        occurred_at=datetime.now(timezone.utc),
        goal_id=goal_id,
        name=name,
    )
    assert event.goal_id == goal_id
    assert event.name == name


@pytest.mark.unit
def test_goal_completed_carries_goal_id_and_user_id() -> None:
    goal_id = GoalId.generate()
    user_id = UserId.generate()
    event = GoalCompleted(
        occurred_at=datetime.now(timezone.utc),
        goal_id=goal_id,
        user_id=user_id,
    )
    assert event.goal_id == goal_id
    assert event.user_id == user_id


@pytest.mark.unit
def test_goal_cancelled_carries_goal_id_and_user_id() -> None:
    goal_id = GoalId.generate()
    user_id = UserId.generate()
    event = GoalCancelled(
        occurred_at=datetime.now(timezone.utc),
        goal_id=goal_id,
        user_id=user_id,
    )
    assert event.goal_id == goal_id
    assert event.user_id == user_id
