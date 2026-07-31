"""`GetWorkoutSessionQuery`: the input to `GetWorkoutSessionHandler`."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.query import Query
from app.domain.workout_session.identifiers import WorkoutSessionId


@dataclass(frozen=True, kw_only=True)
class GetWorkoutSessionQuery(Query):
    """Fetch one WorkoutSession's current state as a
    `WorkoutSessionDTO`."""

    session_id: WorkoutSessionId
