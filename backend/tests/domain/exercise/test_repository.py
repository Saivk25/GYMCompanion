"""Tests for app/domain/exercise/repository.py.

Mirrors `tests/domain/user/test_repository.py` and
`tests/domain/workout/test_repository.py`'s shape — see those files'
docstrings for why the behavior under test is really the shared kernel's
`Repository` abstractness, exercised here through the concrete
`ExerciseRepository`/`Exercise` pairing.
"""

import pytest

from app.domain.exercise.exercise import Exercise
from app.domain.exercise.identifiers import ExerciseId
from app.domain.exercise.repository import ExerciseRepository
from tests.domain.exercise.factories import a_created_exercise


@pytest.mark.unit
def test_exercise_repository_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        ExerciseRepository()  # type: ignore[abstract]


@pytest.mark.unit
def test_a_complete_in_memory_implementation_is_usable() -> None:
    class _InMemoryExerciseRepository(ExerciseRepository):
        def __init__(self) -> None:
            self._exercises: dict[ExerciseId, Exercise] = {}

        def get(self, entity_id: ExerciseId) -> Exercise | None:
            return self._exercises.get(entity_id)

        def add(self, aggregate: Exercise) -> None:
            self._exercises[aggregate.id] = aggregate

        def remove(self, aggregate: Exercise) -> None:
            del self._exercises[aggregate.id]

    repo = _InMemoryExerciseRepository()
    exercise = a_created_exercise()

    assert repo.get(exercise.id) is None

    repo.add(exercise)
    assert repo.get(exercise.id) == exercise

    repo.remove(exercise)
    assert repo.get(exercise.id) is None
