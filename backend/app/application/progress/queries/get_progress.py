"""`GetProgressQuery`: the input to `GetProgressHandler`."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.query import Query
from app.domain.progress.identifiers import ProgressId


@dataclass(frozen=True, kw_only=True)
class GetProgressQuery(Query):
    """Fetch one Progress record by id."""

    progress_id: ProgressId
