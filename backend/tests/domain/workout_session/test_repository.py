"""Tests for app/domain/workout_session/repository.py.

Mirrors `tests/domain/exercise/test_repository.py`'s shape — see that
file's docstring for why the behavior under test is really the shared
kernel's `Repository` abstractness, exercised here through the concrete
`WorkoutSessionRepository`/`WorkoutSession` pairing.
"""

import pytest

from app.domain.user.identifiers import UserId
from app.domain.workout_session.identifiers import WorkoutSessionId
from app.domain.workout_session.repository import WorkoutSessionRepository
from app.domain.workout_session.workout_session import WorkoutSession
from tests.domain.workout_session.factories import a_planned_session


class _InMemoryWorkoutSessionRepository(WorkoutSessionRepository):
    def __init__(self) -> None:
        self._sessions: dict[WorkoutSessionId, WorkoutSession] = {}

    def get(self, entity_id: WorkoutSessionId) -> WorkoutSession | None:
        return self._sessions.get(entity_id)

    def add(self, aggregate: WorkoutSession) -> None:
        self._sessions[aggregate.id] = aggregate

    def remove(self, aggregate: WorkoutSession) -> None:
        del self._sessions[aggregate.id]

    def list_by_user(self, user_id: UserId) -> list[WorkoutSession]:
        return [session for session in self._sessions.values() if session.user_id == user_id]


@pytest.mark.unit
def test_workout_session_repository_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        WorkoutSessionRepository()  # type: ignore[abstract]


@pytest.mark.unit
def test_a_subclass_missing_list_by_user_still_cannot_be_instantiated() -> None:
    class _IncompleteWorkoutSessionRepository(WorkoutSessionRepository):
        def get(self, entity_id: WorkoutSessionId) -> WorkoutSession | None:
            return None

        def add(self, aggregate: WorkoutSession) -> None:
            pass

        def remove(self, aggregate: WorkoutSession) -> None:
            pass

        # list_by_user() deliberately not implemented

    with pytest.raises(TypeError):
        _IncompleteWorkoutSessionRepository()  # type: ignore[abstract]


@pytest.mark.unit
def test_a_complete_in_memory_implementation_is_usable() -> None:
    repo = _InMemoryWorkoutSessionRepository()
    session = a_planned_session()

    assert repo.get(session.id) is None

    repo.add(session)
    assert repo.get(session.id) == session

    repo.remove(session)
    assert repo.get(session.id) is None


@pytest.mark.unit
def test_list_by_user_returns_only_that_users_sessions() -> None:
    repo = _InMemoryWorkoutSessionRepository()
    user_id = UserId.generate()
    mine_first = a_planned_session(user_id=user_id)
    mine_second = a_planned_session(user_id=user_id)
    someone_elses = a_planned_session()
    repo.add(mine_first)
    repo.add(mine_second)
    repo.add(someone_elses)

    result = repo.list_by_user(user_id)

    assert set(result) == {mine_first, mine_second}


@pytest.mark.unit
def test_list_by_user_returns_empty_for_a_user_with_no_sessions() -> None:
    repo = _InMemoryWorkoutSessionRepository()
    assert repo.list_by_user(UserId.generate()) == []
