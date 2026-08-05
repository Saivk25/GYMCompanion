"""`RefreshHandler`: exchanges a still-valid, not-yet-revoked refresh
token for a fresh pair of tokens.

Rotates the refresh token on every use (issues a brand-new one rather
than handing the same one back) — standard refresh-token hygiene: a
refresh token that changes on every use limits how long a stolen-but-
not-yet-used one stays exchangeable, without needing `Credential.
token_version` to move (the caller who is still legitimately using it
should not get logged out by using it).
"""

from __future__ import annotations

from app.application.auth.commands.refresh import RefreshCommand
from app.application.auth.dto.auth_tokens_dto import AuthTokensDTO
from app.application.shared.application_result import ApplicationResult
from app.application.shared.command_handler import CommandHandler
from app.application.shared.unit_of_work import UnitOfWork
from app.domain.auth.credential import Credential
from app.domain.auth.ports import ExpiredTokenError, InvalidTokenError, TokenService
from app.domain.auth.repository import CredentialRepository


class RefreshHandler(CommandHandler[RefreshCommand, AuthTokensDTO]):
    """Validates a refresh token (signature, expiry, and — the
    revocation check — that its embedded `token_version` still matches
    the `Credential`'s current one) and returns a fresh token pair."""

    def __init__(self, *, uow: UnitOfWork, token_service: TokenService) -> None:
        self._uow = uow
        self._token_service = token_service

    def handle(self, request: RefreshCommand) -> ApplicationResult[AuthTokensDTO]:
        try:
            claims = self._token_service.decode_refresh_token(request.refresh_token)
        except (ExpiredTokenError, InvalidTokenError) as exc:
            return ApplicationResult.fail([str(exc)])

        credential: Credential | None = None
        try:
            with self._uow as uow:
                repository = uow.get_repository(
                    CredentialRepository  # type: ignore[type-abstract]
                )
                credential = repository.get(claims.user_id)
        except Exception as exc:
            return ApplicationResult.fail([str(exc)])

        if credential is None or credential.token_version != claims.token_version:
            # Covers both "credential no longer exists" and "this
            # refresh token was revoked" (Credential.revoke_tokens()
            # advanced token_version since this token was issued) — a
            # caller cannot distinguish, and does not need to; both
            # mean "log in again."
            return ApplicationResult.fail(["refresh token has been revoked"])

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
