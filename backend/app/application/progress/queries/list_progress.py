"""`ListProgressQuery`: the input to `ListProgressHandler`."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.query import Query
from app.domain.user.identifiers import UserId


@dataclass(frozen=True, kw_only=True)
class ListProgressQuery(Query):
    """List every Progress record belonging to one User."""

    user_id: UserId
