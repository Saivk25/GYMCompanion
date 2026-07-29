"""Tests for app/domain/exercise/context.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.domain.exercise.context import ExerciseContext
from app.domain.exercise.enums import ExerciseStatus
from app.domain.exercise.value_objects import EquipmentRequirement
from tests.domain.exercise.factories import a_created_exercise, a_fixed_clock


@pytest.mark.unit
def test_from_exercise_snapshots_every_relevant_field() -> None:
    exercise = a_created_exercise()

    context = ExerciseContext.from_exercise(exercise)

    assert context.exercise_id == exercise.id
    assert context.status == ExerciseStatus.ACTIVE
    assert context.name == exercise.name
    assert context.movement_pattern == exercise.movement_pattern
    assert context.difficulty == exercise.difficulty
    assert context.primary_muscles == exercise.primary_muscles
    assert context.secondary_muscles == exercise.secondary_muscles
    assert context.equipment_requirements == exercise.equipment_requirements
    assert context.contraindications == exercise.contraindications


@pytest.mark.unit
def test_is_immutable() -> None:
    exercise = a_created_exercise()
    context = ExerciseContext.from_exercise(exercise)
    with pytest.raises(FrozenInstanceError):
        context.status = ExerciseStatus.DEPRECATED  # type: ignore[misc]


@pytest.mark.unit
def test_does_not_reflect_later_mutations_of_the_source_exercise() -> None:
    """A snapshot is a snapshot — mirrors the equivalent User/Workout
    context tests."""
    exercise = a_created_exercise()
    context = ExerciseContext.from_exercise(exercise)
    new_equipment = frozenset({EquipmentRequirement("barbell")})

    exercise.update(equipment_requirements=new_equipment, clock=a_fixed_clock())

    assert context.equipment_requirements == frozenset()
    assert exercise.equipment_requirements == new_equipment
