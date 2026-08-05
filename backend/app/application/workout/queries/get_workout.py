"""`GetWorkoutQuery`: the input to `GetWorkoutHandler`."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.query import Query
from app.domain.user.identifiers import UserId
from app.domain.workout.identifiers import WorkoutId


@dataclass(frozen=True, kw_only=True)
class GetWorkoutQuery(Query):
    """Fetch one Workout's current state as a `WorkoutDTO`.

    `requester_id` is the authenticated caller — `GetWorkoutHandler`
    compares it against the loaded Workout's own `user_id` via
    `app.application.shared.ownership.ensure_owner` before returning it.
    See `docs/adr/0033-resource-ownership-authorization.md`.
    """

    workout_id: WorkoutId
    requester_id: UserId
