"""Tests for app/domain/goal/repository.py.

Mirrors `tests/domain/readiness/test_repository.py`'s shape — see that
file's docstring for why the behavior under test is really the shared
kernel's `Repository` abstractness (plus this module's own
`list_by_user()` extension), exercised here through the concrete
`GoalRepository`/`Goal` pairing.
"""

import pytest

from app.domain.goal.goal import Goal
from app.domain.goal.identifiers import GoalId
from app.domain.goal.repository import GoalRepository
from app.domain.user.identifiers import UserId
from tests.domain.goal.factories import a_created_goal


class _InMemoryGoalRepository(GoalRepository):
    def __init__(self) -> None:
        self._records: dict[GoalId, Goal] = {}

    def get(self, entity_id: GoalId) -> Goal | None:
        return self._records.get(entity_id)

    def add(self, aggregate: Goal) -> None:
        self._records[aggregate.id] = aggregate

    def remove(self, aggregate: Goal) -> None:
        del self._records[aggregate.id]

    def list_by_user(self, user_id: UserId) -> list[Goal]:
        return [record for record in self._records.values() if record.user_id == user_id]


@pytest.mark.unit
def test_goal_repository_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        GoalRepository()  # type: ignore[abstract]


@pytest.mark.unit
def test_a_subclass_missing_list_by_user_still_cannot_be_instantiated() -> None:
    class _IncompleteGoalRepository(GoalRepository):
        def get(self, entity_id: GoalId) -> Goal | None:
            return None

        def add(self, aggregate: Goal) -> None:
            pass

        def remove(self, aggregate: Goal) -> None:
            pass

        # list_by_user() deliberately not implemented

    with pytest.raises(TypeError):
        _IncompleteGoalRepository()  # type: ignore[abstract]


@pytest.mark.unit
def test_a_complete_in_memory_implementation_is_usable() -> None:
    repo = _InMemoryGoalRepository()
    goal = a_created_goal()

    assert repo.get(goal.id) is None

    repo.add(goal)
    assert repo.get(goal.id) == goal

    repo.remove(goal)
    assert repo.get(goal.id) is None


@pytest.mark.unit
def test_list_by_user_returns_only_that_users_goals() -> None:
    repo = _InMemoryGoalRepository()
    user_id = UserId.generate()
    mine_first = a_created_goal(user_id=user_id)
    mine_second = a_created_goal(user_id=user_id)
    someone_elses = a_created_goal()
    repo.add(mine_first)
    repo.add(mine_second)
    repo.add(someone_elses)

    result = repo.list_by_user(user_id)

    assert set(result) == {mine_first, mine_second}


@pytest.mark.unit
def test_list_by_user_returns_empty_for_a_user_with_no_goals() -> None:
    repo = _InMemoryGoalRepository()
    assert repo.list_by_user(UserId.generate()) == []
