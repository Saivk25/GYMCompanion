"""`ListReadinessQuery`: the input to `ListReadinessHandler`.

The first real caller of `ReadinessRepository.list_by_user()`
(`app.domain.readiness.repository`), added specifically for this query —
see that module's own docstring.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.query import Query
from app.domain.user.identifiers import UserId


@dataclass(frozen=True, kw_only=True)
class ListReadinessQuery(Query):
    """List every Readiness check-in belonging to one User, as
    `ReadinessDTO`s."""

    user_id: UserId
