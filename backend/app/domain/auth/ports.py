"""The two abstract collaborators `Credential`-adjacent Application Layer
handlers depend on but this domain layer does not, and must not,
implement: hashing a password and issuing/decoding a JWT are both
security-critical, library-backed concerns (bcrypt, PyJWT) that belong in
`app/infra/`, never imported here — the same "Domain depends on nothing"
discipline `app.domain.shared_kernel.repository`'s module docstring
argues for `Repository`, and the same shape `app.domain.shared_kernel.
clock.Clock` already establishes for "time" as an injected abstraction
rather than a hidden global or a directly-imported library.

Concrete implementations (`BcryptPasswordHasher`, `JwtTokenService`) live
in `app/infra/security/` and are wired in at the composition root
(`app.composition.container.Container`), never constructed by domain or
application code directly.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.domain.auth.enums import Role
from app.domain.auth.value_objects import PasswordHash
from app.domain.user.identifiers import UserId


class TokenError(Exception):
    """Base for every token-related failure a `TokenService` raises.
    Framework-free on purpose: a caller (an Application Layer handler)
    catches this, or one of its subclasses below, without ever needing
    to know or import whichever JWT library actually raised the
    underlying error.
    """


class InvalidTokenError(TokenError):
    """The token is malformed, has an invalid signature, or is missing
    a claim a valid token must carry. Covers "wrong secret", "tampered
    payload", and "not a JWT at all" alike — a caller does not need to
    distinguish those; all mean "reject this token."
    """


class ExpiredTokenError(TokenError):
    """The token was well-formed and correctly signed, but its `exp`
    claim is in the past. Split from `InvalidTokenError` because a
    caller plausibly wants to distinguish "this token is simply old" (a
    routine, expected outcome for an access token) from "this token is
    actively malformed" (never expected) — see
    `docs/adr/0032-authentication-and-authorization.md`.
    """


@dataclass(frozen=True, kw_only=True)
class AccessTokenClaims:
    """The claims a valid access token decodes to."""

    user_id: UserId
    role: Role


@dataclass(frozen=True, kw_only=True)
class RefreshTokenClaims:
    """The claims a valid refresh token decodes to. `token_version` is
    compared against the current `Credential.token_version` by
    `RefreshHandler` — a mismatch means this refresh token was revoked
    (via `Credential.revoke_tokens()`) since it was issued, even though
    the token itself is still validly signed and unexpired. See
    `Credential.token_version`'s own docstring for the full mechanism.
    """

    user_id: UserId
    token_version: int


class PasswordHasher(ABC):
    """Abstract source of password hashing and verification. See the
    module docstring for why this is an interface owned by the domain
    layer with its real implementation elsewhere."""

    @abstractmethod
    def hash(self, plain_password: str) -> PasswordHash:
        """Hashes `plain_password`, returning an opaque `PasswordHash`.
        Never logs, stores, or otherwise retains the plaintext beyond
        this call."""
        raise NotImplementedError  # pragma: no cover — abstract, always overridden

    @abstractmethod
    def verify(self, plain_password: str, password_hash: PasswordHash) -> bool:
        """Returns whether `plain_password` matches `password_hash`.
        Never raises on a mismatch — a wrong password is an expected,
        common outcome (`POST /login` with a typo), not an error."""
        raise NotImplementedError  # pragma: no cover — abstract, always overridden


class TokenService(ABC):
    """Abstract source of JWT issuance and decoding. See the module
    docstring for why this is an interface owned by the domain layer
    with its real (PyJWT-backed) implementation elsewhere."""

    @property
    @abstractmethod
    def access_token_ttl_seconds(self) -> int:
        """How long a freshly issued access token remains valid, in
        seconds — surfaced so `RegisterHandler`/`LoginHandler`/
        `RefreshHandler` can report it as `AuthTokensDTO.expires_in`
        without duplicating `app.core.config.Settings.
        access_token_ttl_minutes` a second time at the call site."""
        raise NotImplementedError  # pragma: no cover — abstract, always overridden

    @abstractmethod
    def issue_access_token(self, *, user_id: UserId, role: Role) -> str:
        """Issues a short-lived access token carrying `user_id` and
        `role` as claims. See `app.core.config.Settings.
        access_token_ttl_minutes` for the expiry this token is issued
        with."""
        raise NotImplementedError  # pragma: no cover — abstract, always overridden

    @abstractmethod
    def issue_refresh_token(self, *, user_id: UserId, token_version: int) -> str:
        """Issues a long-lived refresh token carrying `user_id` and the
        `token_version` current at issuance time. See
        `app.core.config.Settings.refresh_token_ttl_days` for the
        expiry this token is issued with."""
        raise NotImplementedError  # pragma: no cover — abstract, always overridden

    @abstractmethod
    def decode_access_token(self, token: str) -> AccessTokenClaims:
        """Decodes and validates `token` as an access token, raising
        `ExpiredTokenError` or `InvalidTokenError` if it is not
        currently valid."""
        raise NotImplementedError  # pragma: no cover — abstract, always overridden

    @abstractmethod
    def decode_refresh_token(self, token: str) -> RefreshTokenClaims:
        """Decodes and validates `token` as a refresh token, raising
        `ExpiredTokenError` or `InvalidTokenError` if it is not
        currently valid. Does not itself check `token_version` against
        a `Credential` — see `RefreshTokenClaims`'s own docstring for
        why that comparison belongs to the caller, not this method."""
        raise NotImplementedError  # pragma: no cover — abstract, always overridden
