"""`GetNutritionHandler`: fetches one Nutrition entry's current state as
a `NutritionDTO`.

Same read-side shape as `app.application.workout.handlers.
get_workout_handler.GetWorkoutHandler` — no `Clock`, no
`DomainEventDispatcher`, no `commit()`.
"""

from __future__ import annotations

from app.application.nutrition.dto.nutrition_dto import NutritionDTO
from app.application.nutrition.queries.get_nutrition import GetNutritionQuery
from app.application.shared.application_result import ApplicationResult
from app.application.shared.query_handler import QueryHandler
from app.application.shared.unit_of_work import UnitOfWork
from app.domain.nutrition.nutrition import Nutrition
from app.domain.nutrition.repository import NutritionRepository


class GetNutritionHandler(QueryHandler[GetNutritionQuery, NutritionDTO]):
    """Loads a Nutrition entry and returns it as a `NutritionDTO`, or a
    failed `ApplicationResult` if no such entry exists."""

    def __init__(self, *, uow: UnitOfWork) -> None:
        self._uow = uow

    def handle(self, request: GetNutritionQuery) -> ApplicationResult[NutritionDTO]:
        # `nutrition` is initialized before the `try` (not inside it) so it
        # is always definitely assigned below — see `GetWorkoutHandler`'s
        # identical reasoning.
        nutrition: Nutrition | None = None
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
                nutrition = repository.get(request.nutrition_id)
        except Exception as exc:
            return ApplicationResult.fail([str(exc)])

        if nutrition is None:
            return ApplicationResult.fail([f"nutrition entry {request.nutrition_id} not found"])

        return ApplicationResult.ok(NutritionDTO.from_nutrition(nutrition))
