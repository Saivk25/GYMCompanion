"""Tests for app/domain/workout/context.py."""

from dataclasses import FrozenInstanceError
from datetime import timedelta

import pytest

from app.domain.workout.context import WorkoutContext
from app.domain.workout.enums import WorkoutStatus
from app.domain.workout.value_objects import WorkoutDuration, WorkoutGoal, WorkoutNotes
from tests.domain.workout.factories import a_fixed_clock, a_planned_workout


@pytest.mark.unit
def test_from_workout_snapshots_every_relevant_field() -> None:
    workout = a_planned_workout()
    workout.update_goal(WorkoutGoal("upper body strength"))
    workout.update_notes(WorkoutNotes("Felt strong today"))

    context = WorkoutContext.from_workout(workout)

    assert context.workout_id == workout.id
    assert context.user_id == workout.user_id
    assert context.status == WorkoutStatus.PLANNED
    assert context.name == workout.name
    assert context.planned_date == workout.planned_date
    assert context.goal == WorkoutGoal("upper body strength")
    assert context.notes == WorkoutNotes("Felt strong today")
    assert context.duration is None


@pytest.mark.unit
def test_is_immutable() -> None:
    workout = a_planned_workout()
    context = WorkoutContext.from_workout(workout)
    with pytest.raises(FrozenInstanceError):
        context.status = WorkoutStatus.CANCELLED  # type: ignore[misc]


@pytest.mark.unit
def test_does_not_reflect_later_mutations_of_the_source_workout() -> None:
    """A snapshot is a snapshot — mirrors
    tests/domain/user/test_context.py's equivalent test."""
    workout = a_planned_workout()
    context = WorkoutContext.from_workout(workout)

    clock = a_fixed_clock()
    workout.start(clock=clock)
    workout.complete(duration=WorkoutDuration(timedelta(minutes=45)), clock=clock)

    assert context.status == WorkoutStatus.PLANNED
    assert workout.status == WorkoutStatus.COMPLETED
