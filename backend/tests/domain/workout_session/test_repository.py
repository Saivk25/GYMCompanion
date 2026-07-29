"""Tests for app/domain/workout_session/repository.py.

Mirrors `tests/domain/exercise/test_repository.py`'s shape — see that
file's docstring for why the behavior under test is really the shared
kernel's `Repository` abstractness, exercised here through the concrete
`WorkoutSessionRepository`/`WorkoutSession` pairing.
"""

import pytest

from app.domain.workout_session.identifiers import WorkoutSessionId
from app.domain.workout_session.repository import WorkoutSessionRepository
from app.domain.workout_session.workout_session import WorkoutSession
from tests.domain.workout_session.factories import a_planned_session


@pytest.mark.unit
def test_workout_session_repository_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        WorkoutSessionRepository()  # type: ignore[abstract]


@pytest.mark.unit
def test_a_complete_in_memory_implementation_is_usable() -> None:
    class _InMemoryWorkoutSessionRepository(WorkoutSessionRepository):
        def __init__(self) -> None:
            self._sessions: dict[WorkoutSessionId, WorkoutSession] = {}

        def get(self, entity_id: WorkoutSessionId) -> WorkoutSession | None:
            return self._sessions.get(entity_id)

        def add(self, aggregate: WorkoutSession) -> None:
            self._sessions[aggregate.id] = aggregate

        def remove(self, aggregate: WorkoutSession) -> None:
            del self._sessions[aggregate.id]

    repo = _InMemoryWorkoutSessionRepository()
    session = a_planned_session()

    assert repo.get(session.id) is None

    repo.add(session)
    assert repo.get(session.id) == session

    repo.remove(session)
    assert repo.get(session.id) is None
