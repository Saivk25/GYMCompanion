"""Tests for app/domain/workout_session/events.py.

Immutability, `event_id` auto-generation, and `occurred_at` timezone
enforcement are `DomainEvent` base behavior, already fully covered by
`tests/domain/shared_kernel/test_events.py`. This file only proves each
WorkoutSession-specific event carries the fields it's supposed to.
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.domain.user.identifiers import UserId
from app.domain.workout.identifiers import WorkoutId
from app.domain.workout_session.events import (
    WorkoutSessionAbandoned,
    WorkoutSessionCompleted,
    WorkoutSessionNotesUpdated,
    WorkoutSessionStarted,
)
from app.domain.workout_session.identifiers import WorkoutSessionId
from app.domain.workout_session.value_objects import (
    CompletionPercentage,
    SessionDuration,
    SessionNotes,
)


@pytest.mark.unit
def test_workout_session_started_carries_session_workout_and_user_ids() -> None:
    session_id = WorkoutSessionId.generate()
    workout_id = WorkoutId.generate()
    user_id = UserId.generate()
    event = WorkoutSessionStarted(
        occurred_at=datetime.now(timezone.utc),
        session_id=session_id,
        workout_id=workout_id,
        user_id=user_id,
    )
    assert event.session_id == session_id
    assert event.workout_id == workout_id
    assert event.user_id == user_id


@pytest.mark.unit
def test_workout_session_completed_carries_duration_and_completion_percentage() -> None:
    session_id = WorkoutSessionId.generate()
    duration = SessionDuration(timedelta(minutes=45))
    completion = CompletionPercentage(100.0)
    event = WorkoutSessionCompleted(
        occurred_at=datetime.now(timezone.utc),
        session_id=session_id,
        workout_id=WorkoutId.generate(),
        user_id=UserId.generate(),
        duration=duration,
        completion_percentage=completion,
    )
    assert event.session_id == session_id
    assert event.duration == duration
    assert event.completion_percentage == completion


@pytest.mark.unit
def test_workout_session_abandoned_carries_session_workout_and_user_ids() -> None:
    session_id = WorkoutSessionId.generate()
    workout_id = WorkoutId.generate()
    user_id = UserId.generate()
    event = WorkoutSessionAbandoned(
        occurred_at=datetime.now(timezone.utc),
        session_id=session_id,
        workout_id=workout_id,
        user_id=user_id,
    )
    assert event.session_id == session_id
    assert event.workout_id == workout_id
    assert event.user_id == user_id


@pytest.mark.unit
def test_workout_session_notes_updated_carries_the_full_new_notes() -> None:
    session_id = WorkoutSessionId.generate()
    notes = SessionNotes("Felt strong today.")
    event = WorkoutSessionNotesUpdated(
        occurred_at=datetime.now(timezone.utc),
        session_id=session_id,
        notes=notes,
    )
    assert event.session_id == session_id
    assert event.notes == notes
