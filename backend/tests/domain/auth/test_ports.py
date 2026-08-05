"""Tests for app/domain/auth/ports.py.

Proves each abstract port cannot be instantiated on its own, and that a
minimal, in-memory-style implementation of each is usable — the same
"abstractness + usability" shape every other interface test in this
codebase follows (see `tests/domain/shared_kernel/test_repository.py`).
"""

import pytest

from app.domain.auth.enums import Role
from app.domain.auth.ports import (
    AccessTokenClaims,
    ExpiredTokenError,
    InvalidTokenError,
    PasswordHasher,
    RefreshTokenClaims,
    TokenError,
    TokenService,
)
from app.domain.auth.value_objects import PasswordHash
from app.domain.user.identifiers import UserId

# --- PasswordHasher ---


@pytest.mark.unit
def test_password_hasher_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        PasswordHasher()  # type: ignore[abstract]


@pytest.mark.unit
def test_a_trivial_password_hasher_implementation_is_usable() -> None:
    class _ReversingPasswordHasher(PasswordHasher):
        """Deliberately not a real hash — just enough to prove the
        interface shape is usable; the real bcrypt-backed implementation
        lives in app/infra/security/."""

        def hash(self, plain_password: str) -> PasswordHash:
            return PasswordHash(plain_password[::-1] or "x")

        def verify(self, plain_password: str, password_hash: PasswordHash) -> bool:
            return self.hash(plain_password) == password_hash

    hasher = _ReversingPasswordHasher()
    hashed = hasher.hash("correct horse battery staple")
    assert hasher.verify("correct horse battery staple", hashed) is True
    assert hasher.verify("wrong password", hashed) is False


# --- TokenService ---


@pytest.mark.unit
def test_token_service_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        TokenService()  # type: ignore[abstract]


@pytest.mark.unit
def test_a_trivial_token_service_implementation_is_usable() -> None:
    class _InMemoryTokenService(TokenService):
        @property
        def access_token_ttl_seconds(self) -> int:
            return 900

        def issue_access_token(self, *, user_id: UserId, role: Role) -> str:
            return f"access:{user_id}:{role.value}"

        def issue_refresh_token(self, *, user_id: UserId, token_version: int) -> str:
            return f"refresh:{user_id}:{token_version}"

        def decode_access_token(self, token: str) -> AccessTokenClaims:
            _, user_id, role = token.split(":")
            return AccessTokenClaims(user_id=UserId.parse(user_id), role=Role(role))

        def decode_refresh_token(self, token: str) -> RefreshTokenClaims:
            _, user_id, token_version = token.split(":")
            return RefreshTokenClaims(
                user_id=UserId.parse(user_id), token_version=int(token_version)
            )

    service = _InMemoryTokenService()
    user_id = UserId.generate()

    assert service.access_token_ttl_seconds == 900

    access = service.issue_access_token(user_id=user_id, role=Role.MEMBER)
    claims = service.decode_access_token(access)
    assert claims.user_id == user_id
    assert claims.role == Role.MEMBER

    refresh = service.issue_refresh_token(user_id=user_id, token_version=2)
    refresh_claims = service.decode_refresh_token(refresh)
    assert refresh_claims.user_id == user_id
    assert refresh_claims.token_version == 2


# --- claims dataclasses ---


@pytest.mark.unit
def test_access_token_claims_carries_user_id_and_role() -> None:
    user_id = UserId.generate()
    claims = AccessTokenClaims(user_id=user_id, role=Role.MEMBER)
    assert claims.user_id == user_id
    assert claims.role == Role.MEMBER


@pytest.mark.unit
def test_refresh_token_claims_carries_user_id_and_token_version() -> None:
    user_id = UserId.generate()
    claims = RefreshTokenClaims(user_id=user_id, token_version=5)
    assert claims.user_id == user_id
    assert claims.token_version == 5


# --- error hierarchy ---


@pytest.mark.unit
def test_expired_and_invalid_token_errors_are_token_errors() -> None:
    assert issubclass(ExpiredTokenError, TokenError)
    assert issubclass(InvalidTokenError, TokenError)
