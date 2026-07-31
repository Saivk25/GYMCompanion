"""Tests for app/application/workout/queries/get_workout.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.application.shared.query import Query
from app.application.workout.queries.get_workout import GetWorkoutQuery
from app.domain.workout.identifiers import WorkoutId


@pytest.mark.unit
def test_get_workout_query_is_a_query() -> None:
    assert isinstance(GetWorkoutQuery(workout_id=WorkoutId.generate()), Query)


@pytest.mark.unit
def test_get_workout_query_exposes_its_workout_id() -> None:
    workout_id = WorkoutId.generate()
    query = GetWorkoutQuery(workout_id=workout_id)
    assert query.workout_id == workout_id


@pytest.mark.unit
def test_get_workout_query_is_immutable() -> None:
    query = GetWorkoutQuery(workout_id=WorkoutId.generate())
    with pytest.raises(FrozenInstanceError):
        query.workout_id = WorkoutId.generate()  # type: ignore[misc]
