"""`GetUserQuery`: the input to `GetUserHandler`."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.query import Query
from app.domain.user.identifiers import UserId


@dataclass(frozen=True, kw_only=True)
class GetUserQuery(Query):
    """Fetch one User's current state as a `UserDTO`."""

    user_id: UserId
