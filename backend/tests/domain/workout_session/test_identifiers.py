"""Tests for app/domain/workout_session/identifiers.py.

Deliberately thin — see `tests/domain/user/test_identifiers.py`'s
docstring for why: `WorkoutSessionId`'s generic identifier behavior is the
shared kernel's own `EntityId` behavior, already fully covered by
`tests/domain/shared_kernel/test_identifiers.py`.
"""

import pytest

from app.domain.shared_kernel.identifiers import EntityId
from app.domain.workout_session.identifiers import WorkoutSessionId


@pytest.mark.unit
def test_workout_session_id_is_an_entity_id() -> None:
    assert issubclass(WorkoutSessionId, EntityId)


@pytest.mark.unit
def test_generate_returns_a_workout_session_id() -> None:
    assert isinstance(WorkoutSessionId.generate(), WorkoutSessionId)


@pytest.mark.unit
def test_parse_round_trips_through_str() -> None:
    original = WorkoutSessionId.generate()
    assert WorkoutSessionId.parse(str(original)) == original
