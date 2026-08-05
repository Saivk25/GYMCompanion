"""`LoginHandler`: exchanges an email + password for a fresh pair of
tokens.

Read-only from a persistence standpoint (loads a `Credential`, verifies
a password, issues tokens — nothing is written back), so this needs no
`Clock` and no `DomainEventDispatcher`, the same reasoning
`GetUserHandler` documents for the read-side shape generally. It still
needs `PasswordHasher` and `TokenService`, the two collaborators every
handler in this package may use and no other package may.
"""

from __future__ import annotations

from app.application.auth.commands.login import LoginCommand
from app.application.auth.dto.auth_tokens_dto import AuthTokensDTO
from app.application.shared.application_result import ApplicationResult
from app.application.shared.command_handler import CommandHandler
from app.application.shared.unit_of_work import UnitOfWork
from app.domain.auth.credential import Credential
from app.domain.auth.ports import PasswordHasher, TokenService
from app.domain.auth.repository import CredentialRepository

# One deliberately generic failure message for both "no such email" and
# "wrong password" — never distinguishing the two in what the caller
# sees. Telling an attacker "that email isn't registered" (vs. "wrong
# password") is a real information leak (account enumeration); a
# legitimate caller who mistyped either field gets exactly as much
# help either way.
_INVALID_CREDENTIALS_MESSAGE = "invalid email or password"


class LoginHandler(CommandHandler[LoginCommand, AuthTokensDTO]):
    """Verifies an email + password pair and returns a fresh token
    pair on success, or a failed `ApplicationResult` on any kind of
    mismatch."""

    def __init__(
        self,
        *,
        uow: UnitOfWork,
        password_hasher: PasswordHasher,
        token_service: TokenService,
    ) -> None:
        self._uow = uow
        self._password_hasher = password_hasher
        self._token_service = token_service

    def handle(self, request: LoginCommand) -> ApplicationResult[AuthTokensDTO]:
        credential: Credential | None = None
        try:
            with self._uow as uow:
                repository = uow.get_repository(
                    CredentialRepository  # type: ignore[type-abstract]
                )
                credential = repository.get_by_email(request.email)
        except Exception as exc:
            return ApplicationResult.fail([str(exc)])

        if credential is None or not self._password_hasher.verify(
            request.password, credential.password_hash
        ):
            return ApplicationResult.fail([_INVALID_CREDENTIALS_MESSAGE])

        tokens = AuthTokensDTO(
            access_token=self._token_service.issue_access_token(
                user_id=credential.id, role=credential.role
            ),
            refresh_token=self._token_service.issue_refresh_token(
                user_id=credential.id, token_version=credential.token_version
            ),
            expires_in=self._token_service.access_token_ttl_seconds,
        )
        return ApplicationResult.ok(tokens)
