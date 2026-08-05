"""Tests for app/application/auth/handlers/get_current_user_handler.py."""

import pytest

from app.application.auth.handlers.get_current_user_handler import GetCurrentUserHandler
from app.application.auth.queries.get_current_user import GetCurrentUserQuery
from app.domain.user.identifiers import UserId
from tests.application.auth.factories import (
    FakeCredentialRepository,
    FakeUnitOfWork,
    a_registered_credential,
    a_registered_user,
)
from tests.application.user.factories import FakeUserRepository


@pytest.mark.unit
def test_returns_the_combined_identity() -> None:
    user_id = UserId.generate()
    user = a_registered_user(user_id=user_id)
    credential = a_registered_credential(user_id=user_id)
    uow = FakeUnitOfWork(
        user_repository=FakeUserRepository({user_id: user}),
        credential_repository=FakeCredentialRepository({user_id: credential}),
    )
    handler = GetCurrentUserHandler(uow=uow)

    result = handler.handle(GetCurrentUserQuery(user_id=user_id))

    assert result.success is True
    assert result.value is not None
    assert result.value.user_id == user_id
    assert result.value.email == credential.email


@pytest.mark.unit
def test_fails_when_the_user_does_not_exist() -> None:
    user_id = UserId.generate()
    credential = a_registered_credential(user_id=user_id)
    uow = FakeUnitOfWork(
        user_repository=FakeUserRepository(),
        credential_repository=FakeCredentialRepository({user_id: credential}),
    )
    handler = GetCurrentUserHandler(uow=uow)

    result = handler.handle(GetCurrentUserQuery(user_id=user_id))

    assert result.success is False


@pytest.mark.unit
def test_fails_when_the_credential_does_not_exist() -> None:
    user_id = UserId.generate()
    user = a_registered_user(user_id=user_id)
    uow = FakeUnitOfWork(
        user_repository=FakeUserRepository({user_id: user}),
        credential_repository=FakeCredentialRepository(),
    )
    handler = GetCurrentUserHandler(uow=uow)

    result = handler.handle(GetCurrentUserQuery(user_id=user_id))

    assert result.success is False
