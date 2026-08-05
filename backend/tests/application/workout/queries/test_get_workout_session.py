"""Tests for app/application/workout/queries/get_workout_session.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.application.shared.query import Query
from app.application.workout.queries.get_workout_session import GetWorkoutSessionQuery
from app.domain.user.identifiers import UserId
from app.domain.workout_session.identifiers import WorkoutSessionId


@pytest.mark.unit
def test_get_workout_session_query_is_a_query() -> None:
    assert isinstance(
        GetWorkoutSessionQuery(
            session_id=WorkoutSessionId.generate(), requester_id=UserId.generate()
        ),
        Query,
    )


@pytest.mark.unit
def test_get_workout_session_query_exposes_its_session_id() -> None:
    session_id = WorkoutSessionId.generate()
    query = GetWorkoutSessionQuery(session_id=session_id, requester_id=UserId.generate())
    assert query.session_id == session_id


@pytest.mark.unit
def test_get_workout_session_query_exposes_its_requester_id() -> None:
    requester_id = UserId.generate()
    query = GetWorkoutSessionQuery(
        session_id=WorkoutSessionId.generate(), requester_id=requester_id
    )
    assert query.requester_id == requester_id


@pytest.mark.unit
def test_get_workout_session_query_is_immutable() -> None:
    query = GetWorkoutSessionQuery(
        session_id=WorkoutSessionId.generate(), requester_id=UserId.generate()
    )
    with pytest.raises(FrozenInstanceError):
        query.session_id = WorkoutSessionId.generate()  # type: ignore[misc]
