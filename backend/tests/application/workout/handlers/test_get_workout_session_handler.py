"""Tests for
app/application/workout/handlers/get_workout_session_handler.py."""

import pytest

from app.application.workout.handlers.get_workout_session_handler import GetWorkoutSessionHandler
from app.application.workout.queries.get_workout_session import GetWorkoutSessionQuery
from app.domain.user.identifiers import UserId
from app.domain.workout_session.identifiers import WorkoutSessionId
from tests.application.workout.factories import (
    FakeUnitOfWork,
    FakeWorkoutSessionRepository,
    a_planned_session,
)


@pytest.mark.unit
def test_returns_a_workout_session_dto_for_an_existing_session() -> None:
    session = a_planned_session()
    uow = FakeUnitOfWork(sessions=FakeWorkoutSessionRepository({session.id: session}))
    handler = GetWorkoutSessionHandler(uow=uow)

    result = handler.handle(
        GetWorkoutSessionQuery(session_id=session.id, requester_id=session.user_id)
    )

    assert result.success is True
    assert result.value is not None
    assert result.value.session_id == session.id
    assert result.value.workout_id == session.workout_id


@pytest.mark.unit
def test_a_missing_session_is_reported_as_a_failed_result() -> None:
    uow = FakeUnitOfWork()
    handler = GetWorkoutSessionHandler(uow=uow)
    missing_id = WorkoutSessionId.generate()

    result = handler.handle(
        GetWorkoutSessionQuery(session_id=missing_id, requester_id=UserId.generate())
    )

    assert result.success is False
    assert str(missing_id) in result.errors[0]


@pytest.mark.unit
def test_a_non_owner_requester_is_denied() -> None:
    session = a_planned_session()
    uow = FakeUnitOfWork(sessions=FakeWorkoutSessionRepository({session.id: session}))
    handler = GetWorkoutSessionHandler(uow=uow)

    result = handler.handle(
        GetWorkoutSessionQuery(session_id=session.id, requester_id=UserId.generate())
    )

    assert result.success is False
    assert result.forbidden is True
    assert result.value is None


@pytest.mark.unit
def test_never_commits_since_nothing_was_staged() -> None:
    session = a_planned_session()
    uow = FakeUnitOfWork(sessions=FakeWorkoutSessionRepository({session.id: session}))
    handler = GetWorkoutSessionHandler(uow=uow)

    handler.handle(GetWorkoutSessionQuery(session_id=session.id, requester_id=session.user_id))

    assert uow.committed is False


@pytest.mark.unit
def test_a_repository_get_failure_is_reported_as_a_failed_result() -> None:
    uow = FakeUnitOfWork(sessions=FakeWorkoutSessionRepository(fail_on_get=True))
    handler = GetWorkoutSessionHandler(uow=uow)

    result = handler.handle(
        GetWorkoutSessionQuery(
            session_id=WorkoutSessionId.generate(), requester_id=UserId.generate()
        )
    )

    assert result.success is False
