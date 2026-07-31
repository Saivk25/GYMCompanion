"""Tests for app/application/user/handlers/get_user_handler.py."""

import pytest

from app.application.user.handlers.get_user_handler import GetUserHandler
from app.application.user.queries.get_user import GetUserQuery
from app.domain.user.identifiers import UserId
from app.domain.user.user import User
from app.domain.user.value_objects import AuthMethod, Locale, Timezone
from tests.application.user.factories import FakeUnitOfWork, FakeUserRepository, a_fixed_clock


def _a_registered_user() -> User:
    user = User.register(
        user_id=UserId.generate(),
        locale=Locale("en"),
        timezone=Timezone("UTC"),
        auth_method=AuthMethod("webauthn_passkey"),
        clock=a_fixed_clock(),
    )
    user.pull_domain_events()
    return user


@pytest.mark.unit
def test_returns_a_user_dto_for_an_existing_user() -> None:
    user = _a_registered_user()
    repository = FakeUserRepository({user.id: user})
    uow = FakeUnitOfWork(repository)
    handler = GetUserHandler(uow=uow)

    result = handler.handle(GetUserQuery(user_id=user.id))

    assert result.success is True
    assert result.value is not None
    assert result.value.user_id == user.id
    assert result.value.locale == Locale("en")


@pytest.mark.unit
def test_never_calls_commit_or_rollback_for_a_successful_read() -> None:
    user = _a_registered_user()
    repository = FakeUserRepository({user.id: user})
    uow = FakeUnitOfWork(repository)
    handler = GetUserHandler(uow=uow)

    handler.handle(GetUserQuery(user_id=user.id))

    assert uow.committed is False
    assert uow.rolled_back is False


@pytest.mark.unit
def test_a_missing_user_is_reported_as_a_failed_result() -> None:
    repository = FakeUserRepository()
    uow = FakeUnitOfWork(repository)
    handler = GetUserHandler(uow=uow)
    missing_id = UserId.generate()

    result = handler.handle(GetUserQuery(user_id=missing_id))

    assert result.success is False
    assert str(missing_id) in result.errors[0]
    assert uow.rolled_back is False


@pytest.mark.unit
def test_a_repository_get_failure_is_reported_as_a_failed_result() -> None:
    repository = FakeUserRepository(fail_on_get=True)
    uow = FakeUnitOfWork(repository)
    handler = GetUserHandler(uow=uow)

    result = handler.handle(GetUserQuery(user_id=UserId.generate()))

    assert result.success is False
    assert result.errors
