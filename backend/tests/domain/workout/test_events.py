"""Tests for app/domain/workout/events.py.

Immutability, `event_id` auto-generation, and `occurred_at` timezone
enforcement are `DomainEvent` base behavior, already fully covered by
`tests/domain/shared_kernel/test_events.py`. This file only proves each
Workout-specific event carries the fields it's supposed to.
"""

from datetime import date, datetime, timedelta, timezone

import pytest

from app.domain.user.identifiers import UserId
from app.domain.workout.events import (
    WorkoutCancelled,
    WorkoutCompleted,
    WorkoutPlanned,
    WorkoutStarted,
)
from app.domain.workout.identifiers import WorkoutId
from app.domain.workout.value_objects import WorkoutDate, WorkoutDuration, WorkoutName


@pytest.mark.unit
def test_workout_planned_carries_name_and_planned_date() -> None:
    workout_id = WorkoutId.generate()
    user_id = UserId.generate()
    event = WorkoutPlanned(
        occurred_at=datetime.now(timezone.utc),
        workout_id=workout_id,
        user_id=user_id,
        name=WorkoutName("Push Day"),
        planned_date=WorkoutDate(date(2026, 1, 1)),
    )
    assert event.workout_id == workout_id
    assert event.user_id == user_id
    assert event.name == WorkoutName("Push Day")
    assert event.planned_date == WorkoutDate(date(2026, 1, 1))


@pytest.mark.unit
def test_workout_started_carries_workout_and_user_ids() -> None:
    workout_id = WorkoutId.generate()
    user_id = UserId.generate()
    event = WorkoutStarted(
        occurred_at=datetime.now(timezone.utc),
        workout_id=workout_id,
        user_id=user_id,
    )
    assert event.workout_id == workout_id
    assert event.user_id == user_id


@pytest.mark.unit
def test_workout_completed_carries_the_logged_duration() -> None:
    workout_id = WorkoutId.generate()
    user_id = UserId.generate()
    duration = WorkoutDuration(timedelta(minutes=45))
    event = WorkoutCompleted(
        occurred_at=datetime.now(timezone.utc),
        workout_id=workout_id,
        user_id=user_id,
        duration=duration,
    )
    assert event.workout_id == workout_id
    assert event.user_id == user_id
    assert event.duration == duration


@pytest.mark.unit
def test_workout_cancelled_carries_workout_and_user_ids() -> None:
    workout_id = WorkoutId.generate()
    user_id = UserId.generate()
    event = WorkoutCancelled(
        occurred_at=datetime.now(timezone.utc),
        workout_id=workout_id,
        user_id=user_id,
    )
    assert event.workout_id == workout_id
    assert event.user_id == user_id
