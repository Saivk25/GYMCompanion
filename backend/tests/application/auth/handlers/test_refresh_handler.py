"""Tests for app/application/auth/handlers/refresh_handler.py."""

import pytest

from app.application.auth.commands.refresh import RefreshCommand
from app.application.auth.handlers.refresh_handler import RefreshHandler
from app.domain.user.identifiers import UserId
from tests.application.auth.factories import (
    FakeCredentialRepository,
    FakeTokenService,
    FakeUnitOfWork,
    a_fixed_clock,
    a_registered_credential,
)


@pytest.mark.unit
def test_returns_a_fresh_token_pair_for_a_valid_refresh_token() -> None:
    user_id = UserId.generate()
    credential = a_registered_credential(user_id=user_id)
    repository = FakeCredentialRepository({user_id: credential})
    uow = FakeUnitOfWork(credential_repository=repository)
    token_service = FakeTokenService()
    handler = RefreshHandler(uow=uow, token_service=token_service)
    refresh_token = f"refresh:{user_id}:0"

    result = handler.handle(RefreshCommand(refresh_token=refresh_token))

    assert result.success is True
    assert result.value is not None


@pytest.mark.unit
def test_rotates_the_refresh_token() -> None:
    user_id = UserId.generate()
    credential = a_registered_credential(user_id=user_id)
    repository = FakeCredentialRepository({user_id: credential})
    uow = FakeUnitOfWork(credential_repository=repository)
    token_service = FakeTokenService()
    handler = RefreshHandler(uow=uow, token_service=token_service)

    result = handler.handle(RefreshCommand(refresh_token=f"refresh:{user_id}:0"))

    assert result.value is not None
    assert result.value.refresh_token != f"refresh:{user_id}:0"


@pytest.mark.unit
def test_rejects_an_invalid_token() -> None:
    repository = FakeCredentialRepository()
    uow = FakeUnitOfWork(credential_repository=repository)
    token_service = FakeTokenService(invalid_tokens=frozenset({"garbage"}))
    handler = RefreshHandler(uow=uow, token_service=token_service)

    result = handler.handle(RefreshCommand(refresh_token="garbage"))

    assert result.success is False


@pytest.mark.unit
def test_rejects_an_expired_token() -> None:
    repository = FakeCredentialRepository()
    uow = FakeUnitOfWork(credential_repository=repository)
    token_service = FakeTokenService(expired_tokens=frozenset({"stale-token"}))
    handler = RefreshHandler(uow=uow, token_service=token_service)

    result = handler.handle(RefreshCommand(refresh_token="stale-token"))

    assert result.success is False


@pytest.mark.unit
def test_rejects_a_token_whose_version_has_been_revoked() -> None:
    """The token itself decodes fine (valid signature, not expired), but
    the embedded token_version (0) no longer matches the Credential's
    current one (1, after a logout) — see `Credential.revoke_tokens()`."""
    user_id = UserId.generate()
    credential = a_registered_credential(user_id=user_id)
    credential.revoke_tokens(clock=a_fixed_clock())
    repository = FakeCredentialRepository({user_id: credential})
    uow = FakeUnitOfWork(credential_repository=repository)
    token_service = FakeTokenService()
    handler = RefreshHandler(uow=uow, token_service=token_service)

    result = handler.handle(RefreshCommand(refresh_token=f"refresh:{user_id}:0"))

    assert result.success is False
    assert "revoked" in result.errors[0]


@pytest.mark.unit
def test_rejects_a_token_for_a_credential_that_no_longer_exists() -> None:
    user_id = UserId.generate()
    repository = FakeCredentialRepository()
    uow = FakeUnitOfWork(credential_repository=repository)
    token_service = FakeTokenService()
    handler = RefreshHandler(uow=uow, token_service=token_service)

    result = handler.handle(RefreshCommand(refresh_token=f"refresh:{user_id}:0"))

    assert result.success is False
    assert "revoked" in result.errors[0]
