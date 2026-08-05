"""`DeleteNutritionHandler`: permanently removes an existing Nutrition
entry.

Calls `NutritionRepository.remove()`, not an aggregate method —
`Nutrition` has no delete/soft-delete method of its own and raises no
`NutritionDeleted` event (see `DeleteNutritionCommand`'s own module
docstring for the full reasoning). This handler therefore dispatches an
empty event sequence on every success: `Nutrition.pull_domain_events()`
is never called because the aggregate being removed has none pending
that a deletion should surface, and `DomainEventDispatcher.dispatch(())`
is explicitly well-defined as a no-op (`domain_event_dispatcher.py`'s
own docstring) — there is nothing to lose by calling it uniformly with
every other handler in this package rather than special-casing "skip
dispatch" for this one case.
"""

from __future__ import annotations

from app.application.nutrition.commands.delete_nutrition import DeleteNutritionCommand
from app.application.shared.application_result import ApplicationResult
from app.application.shared.command_handler import CommandHandler
from app.application.shared.domain_event_dispatcher import DomainEventDispatcher
from app.application.shared.ownership import ensure_owner
from app.application.shared.unit_of_work import UnitOfWork
from app.domain.nutrition.identifiers import NutritionId
from app.domain.nutrition.repository import NutritionRepository


class DeleteNutritionHandler(CommandHandler[DeleteNutritionCommand, NutritionId]):
    """Loads a Nutrition entry, removes it, and returns the same
    `NutritionId` on success."""

    def __init__(self, *, uow: UnitOfWork, dispatcher: DomainEventDispatcher) -> None:
        self._uow = uow
        self._dispatcher = dispatcher

    def handle(self, request: DeleteNutritionCommand) -> ApplicationResult[NutritionId]:
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
                if nutrition is None:
                    uow.rollback()
                    return ApplicationResult.fail(
                        [f"nutrition entry {request.nutrition_id} not found"]
                    )

                denial = ensure_owner(owner_id=nutrition.user_id, requester_id=request.requester_id)
                if denial is not None:
                    uow.rollback()
                    return ApplicationResult.forbid([denial])

                repository.remove(nutrition)
                uow.commit()
        except Exception as exc:
            return ApplicationResult.fail([str(exc)])

        self._dispatcher.dispatch(())
        return ApplicationResult.ok(request.nutrition_id)
