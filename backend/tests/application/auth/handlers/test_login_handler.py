"""Tests for app/application/auth/handlers/login_handler.py."""

import pytest

from app.application.auth.commands.login import LoginCommand
from app.application.auth.handlers.login_handler import LoginHandler
from app.domain.auth.credential import Credential
from app.domain.auth.value_objects import Email
from app.domain.user.identifiers import UserId
from tests.application.auth.factories import (
    FakeCredentialRepository,
    FakePasswordHasher,
    FakeTokenService,
    FakeUnitOfWork,
    a_fixed_clock,
)

_A_PASSWORD = "correct horse battery staple"


def _a_handler_with_credential() -> tuple[LoginHandler, UserId]:
    user_id = UserId.generate()
    # Hashed through the same FakePasswordHasher LoginHandler will verify
    # against, rather than hard-coding its output format a second time.
    credential = Credential.register(
        user_id=user_id,
        email=Email("sai@example.com"),
        password_hash=FakePasswordHasher().hash(_A_PASSWORD),
        clock=a_fixed_clock(),
    )
    repository = FakeCredentialRepository({user_id: credential})
    uow = FakeUnitOfWork(credential_repository=repository)
    handler = LoginHandler(
        uow=uow, password_hasher=FakePasswordHasher(), token_service=FakeTokenService()
    )
    return handler, user_id


@pytest.mark.unit
def test_returns_tokens_for_a_correct_password() -> None:
    handler, _ = _a_handler_with_credential()

    result = handler.handle(LoginCommand(email=Email("sai@example.com"), password=_A_PASSWORD))

    assert result.success is True
    assert result.value is not None
    assert result.value.token_type == "bearer"


@pytest.mark.unit
def test_rejects_a_wrong_password() -> None:
    handler, _ = _a_handler_with_credential()

    result = handler.handle(
        LoginCommand(email=Email("sai@example.com"), password="totally wrong password")
    )

    assert result.success is False
    assert result.errors == ("invalid email or password",)


@pytest.mark.unit
def test_rejects_an_unregistered_email_with_the_same_message() -> None:
    """Same failure message as a wrong password — see
    `login_handler.py`'s own docstring on account enumeration."""
    handler, _ = _a_handler_with_credential()

    result = handler.handle(LoginCommand(email=Email("nobody@example.com"), password=_A_PASSWORD))

    assert result.success is False
    assert result.errors == ("invalid email or password",)


@pytest.mark.unit
def test_issues_tokens_scoped_to_the_matched_credential() -> None:
    handler, user_id = _a_handler_with_credential()

    result = handler.handle(LoginCommand(email=Email("sai@example.com"), password=_A_PASSWORD))

    assert result.value is not None
    assert f"access:{user_id}" in result.value.access_token


@pytest.mark.unit
def test_a_repository_failure_is_reported_as_a_failed_result() -> None:
    repository = FakeCredentialRepository(fail_on_get=True)
    uow = FakeUnitOfWork(credential_repository=repository)
    handler = LoginHandler(
        uow=uow, password_hasher=FakePasswordHasher(), token_service=FakeTokenService()
    )

    result = handler.handle(LoginCommand(email=Email("sai@example.com"), password=_A_PASSWORD))

    assert result.success is False
