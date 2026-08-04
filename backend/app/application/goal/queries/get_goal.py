"""`GetGoalQuery`: the input to `GetGoalHandler`."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.query import Query
from app.domain.goal.identifiers import GoalId


@dataclass(frozen=True, kw_only=True)
class GetGoalQuery(Query):
    """Fetch one Goal's current state as a `GoalDTO`."""

    goal_id: GoalId
