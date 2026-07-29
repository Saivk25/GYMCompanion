"""Tests for app/domain/exercise/events.py.

Immutability, `event_id` auto-generation, and `occurred_at` timezone
enforcement are `DomainEvent` base behavior, already fully covered by
`tests/domain/shared_kernel/test_events.py`. This file only proves each
Exercise-specific event carries the fields it's supposed to.
"""

from datetime import datetime, timezone

import pytest

from app.domain.exercise.enums import Difficulty, MovementPattern
from app.domain.exercise.events import ExerciseCreated, ExerciseDeprecated, ExerciseUpdated
from app.domain.exercise.identifiers import ExerciseId
from app.domain.exercise.value_objects import ExerciseName


@pytest.mark.unit
def test_exercise_created_carries_name_movement_pattern_and_difficulty() -> None:
    exercise_id = ExerciseId.generate()
    event = ExerciseCreated(
        occurred_at=datetime.now(timezone.utc),
        exercise_id=exercise_id,
        name=ExerciseName("Barbell Bench Press"),
        movement_pattern=MovementPattern.PUSH,
        difficulty=Difficulty.INTERMEDIATE,
    )
    assert event.exercise_id == exercise_id
    assert event.name == ExerciseName("Barbell Bench Press")
    assert event.movement_pattern is MovementPattern.PUSH
    assert event.difficulty is Difficulty.INTERMEDIATE


@pytest.mark.unit
def test_exercise_updated_carries_exercise_id_and_current_name() -> None:
    exercise_id = ExerciseId.generate()
    event = ExerciseUpdated(
        occurred_at=datetime.now(timezone.utc),
        exercise_id=exercise_id,
        name=ExerciseName("Renamed"),
    )
    assert event.exercise_id == exercise_id
    assert event.name == ExerciseName("Renamed")


@pytest.mark.unit
def test_exercise_deprecated_carries_exercise_id() -> None:
    exercise_id = ExerciseId.generate()
    event = ExerciseDeprecated(occurred_at=datetime.now(timezone.utc), exercise_id=exercise_id)
    assert event.exercise_id == exercise_id
