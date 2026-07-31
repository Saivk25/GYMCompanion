"""`CreateUserHandler`: registers a brand-new User.

Orchestration only — every field on the new `User` is either handed
through verbatim from `CreateUserCommand` or produced by domain code
(`User.register(...)`, `UserId.generate()`); this handler decides
nothing about what makes a User valid. See
`docs/adr/0023-user-application-use-cases.md` for the general shape
every handler in this package follows.
"""

from __future__ import annotations

from app.application.shared.application_result import ApplicationResult
from app.application.shared.command_handler import CommandHandler
from app.application.shared.domain_event_dispatcher import DomainEventDispatcher
from app.application.shared.unit_of_work import UnitOfWork
from app.application.user.commands.create_user import CreateUserCommand
from app.domain.shared_kernel.clock import Clock
from app.domain.user.identifiers import UserId
from app.domain.user.repository import UserRepository
from app.domain.user.user import User


class CreateUserHandler(CommandHandler[CreateUserCommand, UserId]):
    """Registers a new User and returns its freshly generated `UserId`
    on success.

    Constructed once with the collaborators every handler in this
    package needs a variant of: a `UnitOfWork` for the transactional
    boundary, a `DomainEventDispatcher` for publishing what the
    aggregate recorded, and (here, and everywhere a `Clock`-taking
    aggregate method is invoked) a `Clock`.
    """

    def __init__(self, *, uow: UnitOfWork, dispatcher: DomainEventDispatcher, clock: Clock) -> None:
        self._uow = uow
        self._dispatcher = dispatcher
        self._clock = clock

    def handle(self, request: CreateUserCommand) -> ApplicationResult[UserId]:
        """`user_id` is minted here, in application code, matching
        `User.register(...)`'s own documented convention — never
        inside the `Command` itself (see `create_user.py`). A
        `DomainInvariantViolationError` from `User.register(...)`
        (not expected in practice, since every field is already a
        validated value object by the time it reaches this command) is
        raised before the `try` below even begins, so it always
        propagates untouched — see the module-level ADR for why this
        layer never converts an invariant violation into an
        `ApplicationResult` failure. Only a repository/`UnitOfWork`
        failure (e.g. a duplicate id collision a concrete
        implementation's persistence layer detects) is caught and
        reported as a failed `ApplicationResult`.
        """
        user_id = UserId.generate()
        user = User.register(
            user_id=user_id,
            locale=request.locale,
            timezone=request.timezone,
            auth_method=request.auth_method,
            clock=self._clock,
        )

        # No `except DomainInvariantViolationError: raise` guard here, unlike
        # every other handler in this package — `User.register(...)` above
        # is called *before* this `try`, not inside it, so an invariant
        # violation it raises already propagates untouched without this
        # `try` ever seeing it. The `try` below exists solely to translate a
        # repository/`UnitOfWork` failure into a failed `ApplicationResult`.
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
                repository.add(user)
                uow.commit()
        except Exception as exc:
            return ApplicationResult.fail([str(exc)])

        self._dispatcher.dispatch(user.pull_domain_events())
        return ApplicationResult.ok(user_id)
