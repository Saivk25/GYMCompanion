"""Tests for app/domain/workout/repository.py.

Mirrors `tests/domain/user/test_repository.py`'s shape — see that file's
docstring for why the behavior under test is really the shared kernel's
`Repository` abstractness, exercised here through the concrete
`WorkoutRepository`/`Workout` pairing.
"""

import pytest

from app.domain.workout.identifiers import WorkoutId
from app.domain.workout.repository import WorkoutRepository
from app.domain.workout.workout import Workout
from tests.domain.workout.factories import a_planned_workout


@pytest.mark.unit
def test_workout_repository_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        WorkoutRepository()  # type: ignore[abstract]


@pytest.mark.unit
def test_a_complete_in_memory_implementation_is_usable() -> None:
    class _InMemoryWorkoutRepository(WorkoutRepository):
        def __init__(self) -> None:
            self._workouts: dict[WorkoutId, Workout] = {}

        def get(self, entity_id: WorkoutId) -> Workout | None:
            return self._workouts.get(entity_id)

        def add(self, aggregate: Workout) -> None:
            self._workouts[aggregate.id] = aggregate

        def remove(self, aggregate: Workout) -> None:
            del self._workouts[aggregate.id]

    repo = _InMemoryWorkoutRepository()
    workout = a_planned_workout()

    assert repo.get(workout.id) is None

    repo.add(workout)
    assert repo.get(workout.id) == workout

    repo.remove(workout)
    assert repo.get(workout.id) is None
