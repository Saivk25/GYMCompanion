"""`UpdateProfileHandler`: replaces an existing User's profile.

See `docs/adr/0023-user-application-use-cases.md` for the load/
mutate/commit/dispatch shape every mutating handler in this package
follows, and for why `DomainInvariantViolationError` is always
re-raised rather than converted into a failed `ApplicationResult`.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.application.shared.application_result import ApplicationResult
from app.application.shared.command_handler import CommandHandler
from app.application.shared.domain_event_dispatcher import DomainEventDispatcher
from app.application.shared.unit_of_work import UnitOfWork
from app.application.user.commands.update_profile import UpdateProfileCommand
from app.domain.shared_kernel.clock import Clock
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.shared_kernel.events import DomainEvent
from app.domain.user.identifiers import UserId
from app.domain.user.repository import UserRepository


class UpdateProfileHandler(CommandHandler[UpdateProfileCommand, UserId]):
    """Loads a User, replaces its profile, and returns the same
    `UserId` on success."""

    def __init__(self, *, uow: UnitOfWork, dispatcher: DomainEventDispatcher, clock: Clock) -> None:
        self._uow = uow
        self._dispatcher = dispatcher
        self._clock = clock

    def handle(self, request: UpdateProfileCommand) -> ApplicationResult[UserId]:
        # `events` is initialized before the `try` (not inside it) so it is
        # always definitely assigned by the time it's dispatched below —
        # every code path that reaches that line either returned early or
        # ran the `with` block's body to completion, but mypy --strict
        # cannot see that from the try/except shape alone.
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

                user.update_profile(request.profile, clock=self._clock)
                uow.commit()
                events = user.pull_domain_events()
        except DomainInvariantViolationError:
            raise
        except Exception as exc:
            return ApplicationResult.fail([str(exc)])

        self._dispatcher.dispatch(events)
        return ApplicationResult.ok(request.user_id)
