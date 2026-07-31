"""`GetWorkoutQuery`: the input to `GetWorkoutHandler`."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.query import Query
from app.domain.workout.identifiers import WorkoutId


@dataclass(frozen=True, kw_only=True)
class GetWorkoutQuery(Query):
    """Fetch one Workout's current state as a `WorkoutDTO`."""

    workout_id: WorkoutId
