"""`ListProgressHandler`: lists every Progress record belonging to one
User, as `ProgressDTO`s.

Read-side, same shape as `app.application.nutrition.handlers.
list_nutrition_handler.ListNutritionHandler`.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.application.progress.dto.progress_dto import ProgressDTO
from app.application.progress.queries.list_progress import ListProgressQuery
from app.application.shared.application_result import ApplicationResult
from app.application.shared.query_handler import QueryHandler
from app.application.shared.unit_of_work import UnitOfWork
from app.domain.progress.progress import Progress
from app.domain.progress.repository import ProgressRepository


class ListProgressHandler(QueryHandler[ListProgressQuery, tuple[ProgressDTO, ...]]):
    """Loads every Progress record for a User and returns them as
    `ProgressDTO`s, in whatever order `list_by_user()` returns (see that
    method's own docstring — no ordering is implied or applied here)."""

    def __init__(self, *, uow: UnitOfWork) -> None:
        self._uow = uow

    def handle(self, request: ListProgressQuery) -> ApplicationResult[tuple[ProgressDTO, ...]]:
        # `records` is initialized before the `try` (not inside it) so it is
        # always definitely assigned below — see `GetProgressHandler`'s
        # identical reasoning; `()` is itself a legitimate result (a user
        # with no records), not just a typing placeholder.
        records: Sequence[Progress] = ()
        try:
            with self._uow as uow:
                # ProgressRepository has no concrete implementation in this
                # phase (by design); mypy's type-abstract check assumes a
                # type[T] argument might be instantiated, but get_repository
                # only ever uses it as a lookup key, so this is a documented,
                # narrow false positive.
                repository = uow.get_repository(
                    ProgressRepository  # type: ignore[type-abstract]
                )
                records = repository.list_by_user(request.user_id)
        except Exception as exc:
            return ApplicationResult.fail([str(exc)])

        return ApplicationResult.ok(tuple(ProgressDTO.from_progress(record) for record in records))
