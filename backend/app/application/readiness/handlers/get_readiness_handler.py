"""`GetReadinessHandler`: fetches one Readiness check-in's current state
as a `ReadinessDTO`.

Same read-side shape as `app.application.nutrition.handlers.
get_nutrition_handler.GetNutritionHandler` — no `Clock`, no
`DomainEventDispatcher`, no `commit()`.
"""

from __future__ import annotations

from app.application.readiness.dto.readiness_dto import ReadinessDTO
from app.application.readiness.queries.get_readiness import GetReadinessQuery
from app.application.shared.application_result import ApplicationResult
from app.application.shared.query_handler import QueryHandler
from app.application.shared.unit_of_work import UnitOfWork
from app.domain.readiness.readiness import Readiness
from app.domain.readiness.repository import ReadinessRepository


class GetReadinessHandler(QueryHandler[GetReadinessQuery, ReadinessDTO]):
    """Loads a Readiness check-in and returns it as a `ReadinessDTO`, or
    a failed `ApplicationResult` if no such check-in exists."""

    def __init__(self, *, uow: UnitOfWork) -> None:
        self._uow = uow

    def handle(self, request: GetReadinessQuery) -> ApplicationResult[ReadinessDTO]:
        # `readiness` is initialized before the `try` (not inside it) so
        # it is always definitely assigned below — see
        # `GetNutritionHandler`'s identical reasoning.
        readiness: Readiness | None = None
        try:
            with self._uow as uow:
                # ReadinessRepository has no concrete implementation in this
                # phase (by design); mypy's type-abstract check assumes a
                # type[T] argument might be instantiated, but get_repository
                # only ever uses it as a lookup key, so this is a documented,
                # narrow false positive.
                repository = uow.get_repository(
                    ReadinessRepository  # type: ignore[type-abstract]
                )
                readiness = repository.get(request.readiness_id)
        except Exception as exc:
            return ApplicationResult.fail([str(exc)])

        if readiness is None:
            return ApplicationResult.fail([f"readiness check-in {request.readiness_id} not found"])

        return ApplicationResult.ok(ReadinessDTO.from_readiness(readiness))
