"""Tests for app/domain/workout/identifiers.py.

Deliberately thin — see `tests/domain/user/test_identifiers.py`'s
docstring for why: `WorkoutId`'s generic identifier behavior is the shared
kernel's own `EntityId` behavior, already fully covered by
`tests/domain/shared_kernel/test_identifiers.py`.
"""

import pytest

from app.domain.shared_kernel.identifiers import EntityId
from app.domain.workout.identifiers import WorkoutId


@pytest.mark.unit
def test_workout_id_is_an_entity_id() -> None:
    assert issubclass(WorkoutId, EntityId)


@pytest.mark.unit
def test_generate_returns_a_workout_id() -> None:
    assert isinstance(WorkoutId.generate(), WorkoutId)


@pytest.mark.unit
def test_parse_round_trips_through_str() -> None:
    original = WorkoutId.generate()
    assert WorkoutId.parse(str(original)) == original
