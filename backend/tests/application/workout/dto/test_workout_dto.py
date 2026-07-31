"""Tests for app/application/workout/dto/workout_dto.py."""

from dataclasses import FrozenInstanceError
from datetime import timedelta

import pytest

from app.application.workout.dto.workout_dto import WorkoutDTO
from app.domain.workout.enums import WorkoutStatus
from app.domain.workout.value_objects import WorkoutDuration
from tests.application.workout.factories import a_fixed_clock, a_planned_workout


@pytest.mark.unit
def test_from_workout_maps_every_field_for_a_planned_workout() -> None:
    workout = a_planned_workout()

    dto = WorkoutDTO.from_workout(workout)

    assert dto.workout_id == workout.id
    assert dto.user_id == workout.user_id
    assert dto.status == WorkoutStatus.PLANNED
    assert dto.name == workout.name
    assert dto.planned_date == workout.planned_date
    assert dto.planned_at == workout.planned_at
    assert dto.goal is None
    assert dto.notes is None
    assert dto.duration is None
    assert dto.started_at is None
    assert dto.completed_at is None
    assert dto.cancelled_at is None


@pytest.mark.unit
def test_from_workout_reflects_a_completed_workout() -> None:
    workout = a_planned_workout()
    workout.start(clock=a_fixed_clock())
    workout.complete(duration=WorkoutDuration(timedelta(minutes=30)), clock=a_fixed_clock())

    dto = WorkoutDTO.from_workout(workout)

    assert dto.status == WorkoutStatus.COMPLETED
    assert dto.duration == WorkoutDuration(timedelta(minutes=30))
    assert dto.started_at is not None
    assert dto.completed_at is not None


@pytest.mark.unit
def test_workout_dto_is_immutable() -> None:
    dto = WorkoutDTO.from_workout(a_planned_workout())
    with pytest.raises(FrozenInstanceError):
        dto.status = WorkoutStatus.CANCELLED  # type: ignore[misc]
