"""`GetWorkoutSessionQuery`: the input to `GetWorkoutSessionHandler`."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.query import Query
from app.domain.user.identifiers import UserId
from app.domain.workout_session.identifiers import WorkoutSessionId


@dataclass(frozen=True, kw_only=True)
class GetWorkoutSessionQuery(Query):
    """Fetch one WorkoutSession's current state as a
    `WorkoutSessionDTO`.

    `requester_id` is the authenticated caller — `GetWorkoutSessionHandler`
    compares it against the loaded WorkoutSession's own `user_id` via
    `app.application.shared.ownership.ensure_owner` before returning it.
    See `docs/adr/0033-resource-ownership-authorization.md`.
    """

    session_id: WorkoutSessionId
    requester_id: UserId
