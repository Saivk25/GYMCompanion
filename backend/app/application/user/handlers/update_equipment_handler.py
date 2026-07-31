"""`UpdateEquipmentHandler`: replaces the equipment an existing User
owns or regularly has access to.

Same load/mutate/commit/dispatch shape as `UpdatePreferencesHandler` —
see `docs/adr/0023-user-application-use-cases.md`. Calls the
aggregate's own narrow `User.update_equipment(...)`, not
`update_preferences(...)`, even though both ultimately replace the
same `UserPreferences.available_equipment` field — see
`update_equipment.py`'s module docstring for why this command/handler
pair exists separately.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.application.shared.application_result import ApplicationResult
from app.application.shared.command_handler import CommandHandler
from app.application.shared.domain_event_dispatcher import DomainEventDispatcher
from app.application.shared.unit_of_work import UnitOfWork
from app.application.user.commands.update_equipment import UpdateEquipmentCommand
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.shared_kernel.events import DomainEvent
from app.domain.user.identifiers import UserId
from app.domain.user.repository import UserRepository


class UpdateEquipmentHandler(CommandHandler[UpdateEquipmentCommand, UserId]):
    """Loads a User, replaces its available equipment, and returns the
    same `UserId` on success."""

    def __init__(self, *, uow: UnitOfWork, dispatcher: DomainEventDispatcher) -> None:
        self._uow = uow
        self._dispatcher = dispatcher

    def handle(self, request: UpdateEquipmentCommand) -> ApplicationResult[UserId]:
        events: Sequence[DomainEvent] = ()
        try:
            with self._uow as uow:
                # UserRepository has no concrete implementation in this phase
                # (by design); mypy's type-abstract check assumes a type[T]
                # argument might be instantiated, but get_repository only ever
                # uses it as a lookup key, so this is a documented, narrow
                # false positive.
                repository = uow.get_repository(
                    UserRepository  # type: ignore[type-abstract]
                )
                user = repository.get(request.user_id)
                if user is None:
                    uow.rollback()
                    return ApplicationResult.fail([f"user {request.user_id} not found"])

                user.update_equipment(request.available_equipment)
                uow.commit()
                events = user.pull_domain_events()
        except DomainInvariantViolationError:
            raise
        except Exception as exc:
            return ApplicationResult.fail([str(exc)])

        self._dispatcher.dispatch(events)
        return ApplicationResult.ok(request.user_id)
