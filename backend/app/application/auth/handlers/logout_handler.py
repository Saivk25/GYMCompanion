"""`LogoutHandler`: revokes every refresh token issued to a Credential
so far.

Same load/mutate/commit/dispatch shape `UpdateProfileHandler`
documents — `Credential.revoke_tokens()` is the one aggregate method
call, everything else here is orchestration. No `repository.add()`
call after mutating: `TrackingRepository` (`app/infra/repositories/
_tracking.py`) syncs an already-tracked aggregate's current field
values onto its row automatically before `uow.commit()` flushes, the
same mechanism every other in-place aggregate mutation in this
codebase already relies on.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.application.auth.commands.logout import LogoutCommand
from app.application.shared.application_result import ApplicationResult
from app.application.shared.command_handler import CommandHandler
from app.application.shared.domain_event_dispatcher import DomainEventDispatcher
from app.application.shared.unit_of_work import UnitOfWork
from app.domain.auth.repository import CredentialRepository
from app.domain.shared_kernel.clock import Clock
from app.domain.shared_kernel.events import DomainEvent
from app.domain.user.identifiers import UserId


class LogoutHandler(CommandHandler[LogoutCommand, UserId]):
    """Loads the caller's `Credential`, revokes its tokens, and
    returns the same `UserId` on success."""

    def __init__(self, *, uow: UnitOfWork, dispatcher: DomainEventDispatcher, clock: Clock) -> None:
        self._uow = uow
        self._dispatcher = dispatcher
        self._clock = clock

    def handle(self, request: LogoutCommand) -> ApplicationResult[UserId]:
        events: Sequence[DomainEvent] = ()
        try:
            with self._uow as uow:
                repository = uow.get_repository(
                    CredentialRepository  # type: ignore[type-abstract]
                )
                credential = repository.get(request.user_id)
                if credential is None:
                    uow.rollback()
                    return ApplicationResult.fail([f"credential {request.user_id} not found"])

                credential.revoke_tokens(clock=self._clock)
                uow.commit()
                events = credential.pull_domain_events()
        except Exception as exc:
            return ApplicationResult.fail([str(exc)])

        self._dispatcher.dispatch(events)
        return ApplicationResult.ok(request.user_id)
