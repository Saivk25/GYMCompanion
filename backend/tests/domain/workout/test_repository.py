"""Tests for app/domain/workout/repository.py.

Mirrors `tests/domain/user/test_repository.py`'s shape — see that file's
docstring for why the behavior under test is really the shared kernel's
`Repository` abstractness, exercised here through the concrete
`WorkoutRepository`/`Workout` pairing.
"""

import pytest

from app.domain.user.identifiers import UserId
from app.domain.workout.identifiers import WorkoutId
from app.domain.workout.repository import WorkoutRepository
from app.domain.workout.workout import Workout
from tests.domain.workout.factories import a_planned_workout


class _InMemoryWorkoutRepository(WorkoutRepository):
    def __init__(self) -> None:
        self._workouts: dict[WorkoutId, Workout] = {}

    def get(self, entity_id: WorkoutId) -> Workout | None:
        return self._workouts.get(entity_id)

    def add(self, aggregate: Workout) -> None:
        self._workouts[aggregate.id] = aggregate

    def remove(self, aggregate: Workout) -> None:
        del self._workouts[aggregate.id]

    def list_by_user(self, user_id: UserId) -> list[Workout]:
        return [workout for workout in self._workouts.values() if workout.user_id == user_id]


@pytest.mark.unit
def test_workout_repository_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        WorkoutRepository()  # type: ignore[abstract]


@pytest.mark.unit
def test_a_subclass_missing_list_by_user_still_cannot_be_instantiated() -> None:
    class _IncompleteWorkoutRepository(WorkoutRepository):
        def get(self, entity_id: WorkoutId) -> Workout | None:
            return None

        def add(self, aggregate: Workout) -> None:
            pass

        def remove(self, aggregate: Workout) -> None:
            pass

        # list_by_user() deliberately not implemented

    with pytest.raises(TypeError):
        _IncompleteWorkoutRepository()  # type: ignore[abstract]


@pytest.mark.unit
def test_a_complete_in_memory_implementation_is_usable() -> None:
    repo = _InMemoryWorkoutRepository()
    workout = a_planned_workout()

    assert repo.get(workout.id) is None

    repo.add(workout)
    assert repo.get(workout.id) == workout

    repo.remove(workout)
    assert repo.get(workout.id) is None


@pytest.mark.unit
def test_list_by_user_returns_only_that_users_workouts() -> None:
    repo = _InMemoryWorkoutRepository()
    user_id = UserId.generate()
    mine_first = a_planned_workout(user_id=user_id)
    mine_second = a_planned_workout(user_id=user_id)
    someone_elses = a_planned_workout()
    repo.add(mine_first)
    repo.add(mine_second)
    repo.add(someone_elses)

    result = repo.list_by_user(user_id)

    assert set(result) == {mine_first, mine_second}


@pytest.mark.unit
def test_list_by_user_returns_empty_for_a_user_with_no_workouts() -> None:
    repo = _InMemoryWorkoutRepository()
    assert repo.list_by_user(UserId.generate()) == []
