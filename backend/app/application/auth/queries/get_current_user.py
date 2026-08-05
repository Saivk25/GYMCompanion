"""`GetCurrentUserQuery`: the input to `GetCurrentUserHandler`
(`GET /me`)."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.query import Query
from app.domain.user.identifiers import UserId


@dataclass(frozen=True, kw_only=True)
class GetCurrentUserQuery(Query):
    """Fetch the authenticated caller's own identity. `user_id` comes
    from the caller's already-validated access token (the API layer's
    authenticated-user dependency), never from a request body or query
    parameter — see `LogoutCommand`'s identical reasoning."""

    user_id: UserId
