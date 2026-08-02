"""`DeleteProgressHandler`: permanently removes an existing Progress
record.

Calls `ProgressRepository.remove()`, not an aggregate method —
`Progress` has no delete/soft-delete method of its own and raises no
`ProgressDeleted` event (see `DeleteProgressCommand`'s own module
docstring for the full reasoning). This handler therefore dispatches an
empty event sequence on every success, the identical
`DeleteNutritionHandler` (`app.application.nutrition.handlers.
delete_nutrition_handler`) pattern: `DomainEventDispatcher.dispatch(())`
is explicitly well-defined as a no-op, so there is nothing to lose by
calling it uniformly with every other handler in this package rather
than special-casing "skip dispatch." No `ProgressEvaluationRuleEngine`
evaluation either — deletion removes the very record the engine would
evaluate, the same reasoning `DeleteNutritionHandler` documents for
skipping `NutritionRuleEngine`.
"""

from __future__ import annotations

from app.application.progress.commands.delete_progress import DeleteProgressCommand
from app.application.shared.application_result import ApplicationResult
from app.application.shared.command_handler import CommandHandler
from app.application.shared.domain_event_dispatcher import DomainEventDispatcher
from app.application.shared.unit_of_work import UnitOfWork
from app.domain.progress.identifiers import ProgressId
from app.domain.progress.repository import ProgressRepository


class DeleteProgressHandler(CommandHandler[DeleteProgressCommand, ProgressId]):
    """Loads a Progress record, removes it, and returns the same
    `ProgressId` on success."""

    def __init__(self, *, uow: UnitOfWork, dispatcher: DomainEventDispatcher) -> None:
        self._uow = uow
        self._dispatcher = dispatcher

    def handle(self, request: DeleteProgressCommand) -> ApplicationResult[ProgressId]:
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
                if progress is None:
                    uow.rollback()
                    return ApplicationResult.fail(
                        [f"progress record {request.progress_id} not found"]
                    )

                repository.remove(progress)
                uow.commit()
        except Exception as exc:
            return ApplicationResult.fail([str(exc)])

        self._dispatcher.dispatch(())
        return ApplicationResult.ok(request.progress_id)
