"""`ListGoalsQuery`: the input to `ListGoalsHandler`.

The first real caller of `GoalRepository.list_by_user()`
(`app.domain.goal.repository`), added specifically for this query — see
that module's own docstring.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.query import Query
from app.domain.user.identifiers import UserId


@dataclass(frozen=True, kw_only=True)
class ListGoalsQuery(Query):
    """List every Goal belonging to one User, as `GoalDTO`s."""

    user_id: UserId
