"""`ListReadinessHandler`: lists every Readiness check-in belonging to
one User, as `ReadinessDTO`s.

The first real caller of `ReadinessRepository.list_by_user()` — see
that method's own docstring (`app.domain.readiness.repository`) and
`docs/adr/0027-readiness-application-use-cases.md`. Read-side, same
shape as `app.application.nutrition.handlers.list_nutrition_handler.
ListNutritionHandler`.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.application.readiness.dto.readiness_dto import ReadinessDTO
from app.application.readiness.queries.list_readiness import ListReadinessQuery
from app.application.shared.application_result import ApplicationResult
from app.application.shared.query_handler import QueryHandler
from app.application.shared.unit_of_work import UnitOfWork
from app.domain.readiness.readiness import Readiness
from app.domain.readiness.repository import ReadinessRepository


class ListReadinessHandler(QueryHandler[ListReadinessQuery, tuple[ReadinessDTO, ...]]):
    """Loads every Readiness check-in for a User and returns them as
    `ReadinessDTO`s, in whatever order `list_by_user()` returns (see
    that method's own docstring — no ordering is implied or applied
    here)."""

    def __init__(self, *, uow: UnitOfWork) -> None:
        self._uow = uow

    def handle(self, request: ListReadinessQuery) -> ApplicationResult[tuple[ReadinessDTO, ...]]:
        # `entries` is initialized before the `try` (not inside it) so it
        # is always definitely assigned below — see `GetReadinessHandler`'s
        # identical reasoning; `()` is itself a legitimate result (a user
        # with no check-ins), not just a typing placeholder.
        entries: Sequence[Readiness] = ()
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
                entries = repository.list_by_user(request.user_id)
        except Exception as exc:
            return ApplicationResult.fail([str(exc)])

        return ApplicationResult.ok(tuple(ReadinessDTO.from_readiness(entry) for entry in entries))
