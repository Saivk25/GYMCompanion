"""`ListWorkoutsQuery`: the input to `ListWorkoutsHandler`.

The first real caller of `WorkoutRepository.list_by_user()`
(`app.domain.workout.repository`), added specifically for this query —
see that module's own docstring.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.query import Query
from app.domain.user.identifiers import UserId


@dataclass(frozen=True, kw_only=True)
class ListWorkoutsQuery(Query):
    """List every Workout belonging to one User, as `WorkoutDTO`s."""

    user_id: UserId
