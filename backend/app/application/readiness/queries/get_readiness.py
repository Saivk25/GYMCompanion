"""`GetReadinessQuery`: the input to `GetReadinessHandler`."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.query import Query
from app.domain.readiness.identifiers import ReadinessId
from app.domain.user.identifiers import UserId


@dataclass(frozen=True, kw_only=True)
class GetReadinessQuery(Query):
    """Fetch one Readiness check-in's current state as a `ReadinessDTO`.

    `requester_id` is the authenticated caller — `GetReadinessHandler`
    compares it against the loaded check-in's own `user_id` via
    `app.application.shared.ownership.ensure_owner` before returning it.
    See `docs/adr/0033-resource-ownership-authorization.md`.
    """

    readiness_id: ReadinessId
    requester_id: UserId
