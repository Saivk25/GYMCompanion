"""`RegisterHandler`: registers a brand-new User and its login
`Credential` together, then returns a fresh pair of tokens.

The one handler in this codebase that orchestrates two aggregates in a
single unit of work — `app.domain.user.User` (profile/preferences
identity) and `app.domain.auth.Credential` (login identity) — because
`POST /register` is the one caller-facing operation that must create
both at once: a `Credential` with no matching `User` (or vice versa)
is never a valid state this system produces. Both share the same
`UserId`, generated once here and handed to both `register()` calls,
which is what keeps them a matched pair without either aggregate
knowing the other exists.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.application.auth.commands.register import RegisterCommand
from app.application.auth.dto.auth_tokens_dto import AuthTokensDTO
from app.application.shared.application_result import ApplicationResult
from app.application.shared.command_handler import CommandHandler
from app.application.shared.domain_event_dispatcher import DomainEventDispatcher
from app.application.shared.unit_of_work import UnitOfWork
from app.domain.auth.credential import Credential
from app.domain.auth.ports import PasswordHasher, TokenService
from app.domain.auth.repository import CredentialRepository
from app.domain.shared_kernel.clock import Clock
from app.domain.shared_kernel.events import DomainEvent
from app.domain.user.identifiers import UserId
from app.domain.user.repository import UserRepository
from app.domain.user.user import User
from app.domain.user.value_objects import AuthMethod

# The `AuthMethod` a User registered through this password-based flow
# is stamped with. A bare string, not a closed enum — see
# `app.domain.user.value_objects.AuthMethod`'s own docstring, which
# names this exact scenario ("infrastructure/security concern... not a
# business rule the domain layer should hard-code a fixed list of") and
# is why adding this value requires no change to that type.
_PASSWORD_AUTH_METHOD = AuthMethod("password")


class RegisterHandler(CommandHandler[RegisterCommand, AuthTokensDTO]):
    """Creates a new `User` + `Credential` pair and returns a fresh
    token pair for the caller to use immediately — registration
    doubles as the first login, matching how every mobile app's
    sign-up flow actually behaves (no separate "now go log in" step)."""

    def __init__(
        self,
        *,
        uow: UnitOfWork,
        dispatcher: DomainEventDispatcher,
        clock: Clock,
        password_hasher: PasswordHasher,
        token_service: TokenService,
    ) -> None:
        self._uow = uow
        self._dispatcher = dispatcher
        self._clock = clock
        self._password_hasher = password_hasher
        self._token_service = token_service

    def handle(self, request: RegisterCommand) -> ApplicationResult[AuthTokensDTO]:
        # `events` is initialized before the `try` for the same
        # definitely-assigned reasoning `UpdateProfileHandler` documents.
        events: Sequence[DomainEvent] = ()
        try:
            with self._uow as uow:
                credential_repository = uow.get_repository(
                    CredentialRepository  # type: ignore[type-abstract]
                )
                # A friendlier, immediate rejection for the common case
                # (retyping an already-registered email) — belt-and-
                # suspenders alongside the database's own unique
                # constraint (`app/infra/repositories/
                # credential_repository.py`), which is what actually
                # closes the race a concurrent duplicate registration
                # could otherwise slip through between this check and
                # the insert below.
                if credential_repository.get_by_email(request.email) is not None:
                    uow.rollback()
                    return ApplicationResult.fail(["email already registered"])

                user_id = UserId.generate()
                user = User.register(
                    user_id=user_id,
                    locale=request.locale,
                    timezone=request.timezone,
                    auth_method=_PASSWORD_AUTH_METHOD,
                    clock=self._clock,
                )
                credential = Credential.register(
                    user_id=user_id,
                    email=request.email,
                    password_hash=self._password_hasher.hash(request.password),
                    clock=self._clock,
                )

                user_repository = uow.get_repository(
                    UserRepository  # type: ignore[type-abstract]
                )
                user_repository.add(user)
                credential_repository.add(credential)
                uow.commit()
                events = [*user.pull_domain_events(), *credential.pull_domain_events()]
        except Exception as exc:
            return ApplicationResult.fail([str(exc)])

        self._dispatcher.dispatch(events)

        tokens = AuthTokensDTO(
            access_token=self._token_service.issue_access_token(
                user_id=user_id, role=credential.role
            ),
            refresh_token=self._token_service.issue_refresh_token(
                user_id=user_id, token_version=credential.token_version
            ),
            expires_in=self._token_service.access_token_ttl_seconds,
        )
        return ApplicationResult.ok(tokens)
