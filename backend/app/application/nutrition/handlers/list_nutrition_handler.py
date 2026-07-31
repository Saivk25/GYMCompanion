"""`ListNutritionHandler`: lists every Nutrition entry belonging to one
User, as `NutritionDTO`s.

The first real caller of `NutritionRepository.list_by_user()` — see
that method's own docstring (`app.domain.nutrition.repository`) and
`docs/adr/0025-nutrition-application-use-cases.md`. Read-side, same
shape as `app.application.workout.handlers.list_workouts_handler.
ListWorkoutsHandler`.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.application.nutrition.dto.nutrition_dto import NutritionDTO
from app.application.nutrition.queries.list_nutrition import ListNutritionQuery
from app.application.shared.application_result import ApplicationResult
from app.application.shared.query_handler import QueryHandler
from app.application.shared.unit_of_work import UnitOfWork
from app.domain.nutrition.nutrition import Nutrition
from app.domain.nutrition.repository import NutritionRepository


class ListNutritionHandler(QueryHandler[ListNutritionQuery, tuple[NutritionDTO, ...]]):
    """Loads every Nutrition entry for a User and returns them as
    `NutritionDTO`s, in whatever order `list_by_user()` returns (see
    that method's own docstring — no ordering is implied or applied
    here)."""

    def __init__(self, *, uow: UnitOfWork) -> None:
        self._uow = uow

    def handle(self, request: ListNutritionQuery) -> ApplicationResult[tuple[NutritionDTO, ...]]:
        # `entries` is initialized before the `try` (not inside it) so it is
        # always definitely assigned below — see `GetNutritionHandler`'s
        # identical reasoning; `()` is itself a legitimate result (a user
        # with no entries), not just a typing placeholder.
        entries: Sequence[Nutrition] = ()
        try:
            with self._uow as uow:
                # NutritionRepository has no concrete implementation in this
                # phase (by design); mypy's type-abstract check assumes a
                # type[T] argument might be instantiated, but get_repository
                # only ever uses it as a lookup key, so this is a documented,
                # narrow false positive.
                repository = uow.get_repository(
                    NutritionRepository  # type: ignore[type-abstract]
                )
                entries = repository.list_by_user(request.user_id)
        except Exception as exc:
            return ApplicationResult.fail([str(exc)])

        return ApplicationResult.ok(tuple(NutritionDTO.from_nutrition(entry) for entry in entries))
