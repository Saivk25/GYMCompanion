"""`UserExistsQuery`: the input to `UserExistsHandler`.

A distinct query from `GetUserQuery`, not a thin wrapper around it,
because the two have different success/failure shapes: for
`GetUserQuery`, "no such user" is the one thing that makes the query
fail (there's no `UserDTO` to return). For `UserExistsQuery`, "no such
user" is not a failure at all — `False` is a perfectly successful
answer to "does this user exist." Collapsing them onto one query would
force one of the two handlers to misuse `ApplicationResult.success`
against its own documented meaning. See
`user_exists_handler.py`.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.query import Query
from app.domain.user.identifiers import UserId


@dataclass(frozen=True, kw_only=True)
class UserExistsQuery(Query):
    """Check whether a User with this id exists."""

    user_id: UserId
