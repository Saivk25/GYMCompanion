"""`GetProgressQuery`: the input to `GetProgressHandler`."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.query import Query
from app.domain.progress.identifiers import ProgressId
from app.domain.user.identifiers import UserId


@dataclass(frozen=True, kw_only=True)
class GetProgressQuery(Query):
    """Fetch one Progress record by id.

    `requester_id` is the authenticated caller — `GetProgressHandler`
    compares it against the loaded record's own `user_id` via
    `app.application.shared.ownership.ensure_owner` before returning it.
    See `docs/adr/0033-resource-ownership-authorization.md`.
    """

    progress_id: ProgressId
    requester_id: UserId
