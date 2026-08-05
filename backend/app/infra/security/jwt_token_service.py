"""`JwtTokenService`: the PyJWT-backed implementation of
`app.domain.auth.ports.TokenService`.

Access and refresh tokens are both plain JWTs signed with the same
`Settings.secret_key` (HS256 by default — symmetric signing is
sufficient here since this service both issues and verifies every
token itself; there is no separate, less-trusted verifier that would
need only a public key). They are told apart by an `is_refresh` claim
and validated accordingly — `decode_access_token` rejects a refresh
token presented as one, and vice versa, so a stolen refresh token
cannot be replayed as a (shorter-lived, differently-scoped) access
token just because both are valid JWTs signed with the same key.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.core.config import Settings
from app.domain.auth.enums import Role
from app.domain.auth.ports import (
    AccessTokenClaims,
    ExpiredTokenError,
    InvalidTokenError,
    RefreshTokenClaims,
    TokenService,
)
from app.domain.user.identifiers import UserId

_SUBJECT_CLAIM = "sub"
_ROLE_CLAIM = "role"
_TOKEN_VERSION_CLAIM = "token_version"  # noqa: S105 — a claim name, not a credential
_IS_REFRESH_CLAIM = "is_refresh"


class JwtTokenService(TokenService):
    """Issues and decodes JWTs via PyJWT, signed with `settings.secret_key`.

    Constructed once at the composition root (`app.composition.container.
    Container`) from the process's own `Settings` — never constructed
    ad hoc, so every token issued and verified during one process's
    lifetime uses the exact same key/algorithm/TTL configuration.
    """

    def __init__(self, settings: Settings) -> None:
        self._secret_key = settings.secret_key
        self._algorithm = settings.jwt_algorithm
        self._access_ttl = timedelta(minutes=settings.access_token_ttl_minutes)
        self._refresh_ttl = timedelta(days=settings.refresh_token_ttl_days)

    @property
    def access_token_ttl_seconds(self) -> int:
        return int(self._access_ttl.total_seconds())

    def issue_access_token(self, *, user_id: UserId, role: Role) -> str:
        return self._encode(
            {
                _SUBJECT_CLAIM: str(user_id),
                _ROLE_CLAIM: role.value,
                _IS_REFRESH_CLAIM: False,
            },
            ttl=self._access_ttl,
        )

    def issue_refresh_token(self, *, user_id: UserId, token_version: int) -> str:
        return self._encode(
            {
                _SUBJECT_CLAIM: str(user_id),
                _TOKEN_VERSION_CLAIM: token_version,
                _IS_REFRESH_CLAIM: True,
            },
            ttl=self._refresh_ttl,
        )

    def decode_access_token(self, token: str) -> AccessTokenClaims:
        claims = self._decode(token)
        if claims.get(_IS_REFRESH_CLAIM) is not False:
            raise InvalidTokenError("not an access token")
        try:
            return AccessTokenClaims(
                user_id=UserId.parse(claims[_SUBJECT_CLAIM]), role=Role(claims[_ROLE_CLAIM])
            )
        except (KeyError, ValueError) as exc:
            raise InvalidTokenError(f"malformed access token claims: {exc}") from exc

    def decode_refresh_token(self, token: str) -> RefreshTokenClaims:
        claims = self._decode(token)
        if claims.get(_IS_REFRESH_CLAIM) is not True:
            raise InvalidTokenError("not a refresh token")
        try:
            return RefreshTokenClaims(
                user_id=UserId.parse(claims[_SUBJECT_CLAIM]),
                token_version=int(claims[_TOKEN_VERSION_CLAIM]),
            )
        except (KeyError, ValueError) as exc:
            raise InvalidTokenError(f"malformed refresh token claims: {exc}") from exc

    def _encode(self, claims: dict[str, Any], *, ttl: timedelta) -> str:
        now = datetime.now(timezone.utc)
        payload = {**claims, "iat": now, "exp": now + ttl}
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def _decode(self, token: str) -> dict[str, Any]:
        try:
            decoded: dict[str, Any] = jwt.decode(
                token, self._secret_key, algorithms=[self._algorithm]
            )
        except jwt.ExpiredSignatureError as exc:
            raise ExpiredTokenError("token has expired") from exc
        except jwt.InvalidTokenError as exc:
            # PyJWT's own broad base exception (bad signature, malformed
            # structure, wrong algorithm, ...) — everything that isn't
            # specifically "expired" collapses to this codebase's
            # equally broad InvalidTokenError, matching that type's own
            # documented scope ("a caller does not need to distinguish").
            raise InvalidTokenError(f"invalid token: {exc}") from exc
        return decoded
