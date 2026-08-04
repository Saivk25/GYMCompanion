"""`DeleteReadinessHandler`: permanently removes an existing Readiness
check-in.

Calls `ReadinessRepository.remove()`, not an aggregate method —
`Readiness` has no delete/soft-delete method of its own and raises no
`ReadinessDeleted` event (see `DeleteReadinessCommand`'s own module
docstring for the full reasoning). This handler therefore dispatches an
empty event sequence on every success, the same "dispatch `()`
uniformly rather than special-case skip" choice
`DeleteNutritionHandler`/`DeleteProgressHandler` already make —
`DomainEventDispatcher.dispatch(())` is explicitly well-defined as a
no-op.
"""

from __future__ import annotations

from app.application.readiness.commands.delete_readiness import DeleteReadinessCommand
from app.application.shared.application_result import ApplicationResult
from app.application.shared.command_handler import CommandHandler
from app.application.shared.domain_event_dispatcher import DomainEventDispatcher
from app.application.shared.unit_of_work import UnitOfWork
from app.domain.readiness.identifiers import ReadinessId
from app.domain.readiness.repository import ReadinessRepository


class DeleteReadinessHandler(CommandHandler[DeleteReadinessCommand, ReadinessId]):
    """Loads a Readiness check-in, removes it, and returns the same
    `ReadinessId` on success."""

    def __init__(self, *, uow: UnitOfWork, dispatcher: DomainEventDispatcher) -> None:
        self._uow = uow
        self._dispatcher = dispatcher

    def handle(self, request: DeleteReadinessCommand) -> ApplicationResult[ReadinessId]:
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
                if readiness is None:
                    uow.rollback()
                    return ApplicationResult.fail(
                        [f"readiness check-in {request.readiness_id} not found"]
                    )

                repository.remove(readiness)
                uow.commit()
        except Exception as exc:
            return ApplicationResult.fail([str(exc)])

        self._dispatcher.dispatch(())
        return ApplicationResult.ok(request.readiness_id)
