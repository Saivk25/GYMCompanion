"""Tests for app/domain/goal/repository.py.

Mirrors `tests/domain/readiness/test_repository.py`'s shape — see that
file's docstring for why the behavior under test is really the shared
kernel's `Repository` abstractness, exercised here through the concrete
`GoalRepository`/`Goal` pairing.
"""

import pytest

from app.domain.goal.goal import Goal
from app.domain.goal.identifiers import GoalId
from app.domain.goal.repository import GoalRepository
from tests.domain.goal.factories import a_created_goal


@pytest.mark.unit
def test_goal_repository_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        GoalRepository()  # type: ignore[abstract]


@pytest.mark.unit
def test_a_complete_in_memory_implementation_is_usable() -> None:
    class _InMemoryGoalRepository(GoalRepository):
        def __init__(self) -> None:
            self._records: dict[GoalId, Goal] = {}

        def get(self, entity_id: GoalId) -> Goal | None:
            return self._records.get(entity_id)

        def add(self, aggregate: Goal) -> None:
            self._records[aggregate.id] = aggregate

        def remove(self, aggregate: Goal) -> None:
            del self._records[aggregate.id]

    repo = _InMemoryGoalRepository()
    goal = a_created_goal()

    assert repo.get(goal.id) is None

    repo.add(goal)
    assert repo.get(goal.id) == goal

    repo.remove(goal)
    assert repo.get(goal.id) is None
