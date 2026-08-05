"""`GetProgressHandler`: fetches one Progress record's current state as
a `ProgressDTO`.

Same read-side shape as `app.application.nutrition.handlers.
get_nutrition_handler.GetNutritionHandler` — no `Clock`, no
`DomainEventDispatcher`, no `commit()`.
"""

from __future__ import annotations

from app.application.progress.dto.progress_dto import ProgressDTO
from app.application.progress.queries.get_progress import GetProgressQuery
from app.application.shared.application_result import ApplicationResult
from app.application.shared.ownership import ensure_owner
from app.application.shared.query_handler import QueryHandler
from app.application.shared.unit_of_work import UnitOfWork
from app.domain.progress.progress import Progress
from app.domain.progress.repository import ProgressRepository


class GetProgressHandler(QueryHandler[GetProgressQuery, ProgressDTO]):
    """Loads a Progress record and returns it as a `ProgressDTO`, or a
    failed `ApplicationResult` if no such record exists."""

    def __init__(self, *, uow: UnitOfWork) -> None:
        self._uow = uow

    def handle(self, request: GetProgressQuery) -> ApplicationResult[ProgressDTO]:
        # `progress` is initialized before the `try` (not inside it) so it
        # is always definitely assigned below — see `GetNutritionHandler`'s
        # identical reasoning.
        progress: Progress | None = None
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
                progress = repository.get(request.progress_id)
        except Exception as exc:
            return ApplicationResult.fail([str(exc)])

        if progress is None:
            return ApplicationResult.fail([f"progress record {request.progress_id} not found"])

        denial = ensure_owner(owner_id=progress.user_id, requester_id=request.requester_id)
        if denial is not None:
            return ApplicationResult.forbid([denial])

        return ApplicationResult.ok(ProgressDTO.from_progress(progress))
