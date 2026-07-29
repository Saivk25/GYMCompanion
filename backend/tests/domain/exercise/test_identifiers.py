"""Tests for app/domain/exercise/identifiers.py.

Deliberately thin — see `tests/domain/user/test_identifiers.py`'s
docstring for why: `ExerciseId`'s generic identifier behavior is the
shared kernel's own `EntityId` behavior, already fully covered by
`tests/domain/shared_kernel/test_identifiers.py`.
"""

import pytest

from app.domain.exercise.identifiers import ExerciseId
from app.domain.shared_kernel.identifiers import EntityId


@pytest.mark.unit
def test_exercise_id_is_an_entity_id() -> None:
    assert issubclass(ExerciseId, EntityId)


@pytest.mark.unit
def test_generate_returns_an_exercise_id() -> None:
    assert isinstance(ExerciseId.generate(), ExerciseId)


@pytest.mark.unit
def test_parse_round_trips_through_str() -> None:
    original = ExerciseId.generate()
    assert ExerciseId.parse(str(original)) == original
