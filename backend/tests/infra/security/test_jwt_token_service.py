"""Tests for app/infra/security/jwt_token_service.py."""

import pytest

from app.core.config import Settings
from app.domain.auth.enums import Role
from app.domain.auth.ports import ExpiredTokenError, InvalidTokenError
from app.domain.user.identifiers import UserId
from app.infra.security.jwt_token_service import JwtTokenService

_A_SECRET = "a-real-generated-secret-for-testing-only"


def _a_service(**overrides: object) -> JwtTokenService:
    overrides.setdefault("secret_key", _A_SECRET)
    settings = Settings(**overrides)  # type: ignore[arg-type]
    return JwtTokenService(settings)


# --- access tokens ---


@pytest.mark.unit
def test_issued_access_token_decodes_to_the_same_claims() -> None:
    service = _a_service()
    user_id = UserId.generate()

    token = service.issue_access_token(user_id=user_id, role=Role.MEMBER)
    claims = service.decode_access_token(token)

    assert claims.user_id == user_id
    assert claims.role == Role.MEMBER


@pytest.mark.unit
def test_access_token_ttl_seconds_matches_settings() -> None:
    service = _a_service(access_token_ttl_minutes=15)
    assert service.access_token_ttl_seconds == 900


@pytest.mark.unit
def test_decode_access_token_rejects_an_expired_token() -> None:
    service = _a_service(access_token_ttl_minutes=-1)
    token = service.issue_access_token(user_id=UserId.generate(), role=Role.MEMBER)

    with pytest.raises(ExpiredTokenError):
        service.decode_access_token(token)


@pytest.mark.unit
def test_decode_access_token_rejects_a_refresh_token() -> None:
    service = _a_service()
    refresh_token = service.issue_refresh_token(user_id=UserId.generate(), token_version=0)

    with pytest.raises(InvalidTokenError):
        service.decode_access_token(refresh_token)


@pytest.mark.unit
def test_decode_access_token_rejects_garbage() -> None:
    service = _a_service()

    with pytest.raises(InvalidTokenError):
        service.decode_access_token("not.a.jwt")


@pytest.mark.unit
def test_decode_access_token_rejects_a_token_signed_with_a_different_secret() -> None:
    issuer = _a_service()
    verifier = _a_service(secret_key="a-completely-different-secret-value")
    token = issuer.issue_access_token(user_id=UserId.generate(), role=Role.MEMBER)

    with pytest.raises(InvalidTokenError):
        verifier.decode_access_token(token)


# --- refresh tokens ---


@pytest.mark.unit
def test_issued_refresh_token_decodes_to_the_same_claims() -> None:
    service = _a_service()
    user_id = UserId.generate()

    token = service.issue_refresh_token(user_id=user_id, token_version=3)
    claims = service.decode_refresh_token(token)

    assert claims.user_id == user_id
    assert claims.token_version == 3


@pytest.mark.unit
def test_decode_refresh_token_rejects_an_expired_token() -> None:
    service = _a_service(refresh_token_ttl_days=-1)
    token = service.issue_refresh_token(user_id=UserId.generate(), token_version=0)

    with pytest.raises(ExpiredTokenError):
        service.decode_refresh_token(token)


@pytest.mark.unit
def test_decode_refresh_token_rejects_an_access_token() -> None:
    service = _a_service()
    access_token = service.issue_access_token(user_id=UserId.generate(), role=Role.MEMBER)

    with pytest.raises(InvalidTokenError):
        service.decode_refresh_token(access_token)
