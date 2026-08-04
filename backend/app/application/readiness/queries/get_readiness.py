"""`GetReadinessQuery`: the input to `GetReadinessHandler`."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.query import Query
from app.domain.readiness.identifiers import ReadinessId


@dataclass(frozen=True, kw_only=True)
class GetReadinessQuery(Query):
    """Fetch one Readiness check-in's current state as a `ReadinessDTO`."""

    readiness_id: ReadinessId
