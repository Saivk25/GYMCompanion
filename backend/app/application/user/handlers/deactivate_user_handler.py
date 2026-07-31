"""`DeactivateUserHandler`: suspends an existing, currently-Active
User.

Same load/mutate/commit/dispatch shape as every other mutating handler
in this package — see
`docs/adr/0023-user-application-use-cases.md`. Calls `User.suspend()`,
not a nonexistent `User.deactivate()` — see `deactivate_user.py`'s
module docstring for why. `user.suspend()` raises
`DomainInvariantViolationError` if the user isn't currently Active
(`user.py`'s transition table); like every other invariant violation,
this handler lets it propagate rather than converting it into a failed
`ApplicationResult` — see the module-level ADR.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.application.shared.application_result import ApplicationResult
from app.application.shared.command_handler import CommandHandler
from app.application.shared.domain_event_dispatcher import DomainEventDispatcher
from app.application.shared.unit_of_work import UnitOfWork
from app.application.user.commands.deactivate_user import DeactivateUserCommand
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.shared_kernel.events import DomainEvent
from app.domain.user.identifiers import UserId
from app.domain.user.repository import UserRepository


class DeactivateUserHandler(CommandHandler[DeactivateUserCommand, UserId]):
    """Loads a User, suspends it, and returns the same `UserId` on
    success."""

    def __init__(self, *, uow: UnitOfWork, dispatcher: DomainEventDispatcher) -> None:
        self._uow = uow
        self._dispatcher = dispatcher

    def handle(self, request: DeactivateUserCommand) -> ApplicationResult[UserId]:
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

                user.suspend()
                uow.commit()
                events = user.pull_domain_events()
        except DomainInvariantViolationError:
            raise
        except Exception as exc:
            return ApplicationResult.fail([str(exc)])

        self._dispatcher.dispatch(events)
        return ApplicationResult.ok(request.user_id)
