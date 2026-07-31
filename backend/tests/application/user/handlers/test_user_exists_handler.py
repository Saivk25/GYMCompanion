"""Tests for app/application/user/handlers/user_exists_handler.py."""

import pytest

from app.application.user.handlers.user_exists_handler import UserExistsHandler
from app.application.user.queries.user_exists import UserExistsQuery
from app.domain.user.identifiers import UserId
from app.domain.user.user import User
from app.domain.user.value_objects import AuthMethod, Locale, Timezone
from tests.application.user.factories import FakeUnitOfWork, FakeUserRepository, a_fixed_clock


def _a_registered_user() -> User:
    return User.register(
        user_id=UserId.generate(),
        locale=Locale("en"),
        timezone=Timezone("UTC"),
        auth_method=AuthMethod("webauthn_passkey"),
        clock=a_fixed_clock(),
    )


@pytest.mark.unit
def test_reports_true_for_an_existing_user() -> None:
    user = _a_registered_user()
    repository = FakeUserRepository({user.id: user})
    uow = FakeUnitOfWork(repository)
    handler = UserExistsHandler(uow=uow)

    result = handler.handle(UserExistsQuery(user_id=user.id))

    assert result.success is True
    assert result.value is True


@pytest.mark.unit
def test_reports_false_for_a_missing_user_as_a_success_not_a_failure() -> None:
    """The whole point of this query being distinct from `GetUserQuery`
    — "no such user" is a successful `False`, not a failed result."""
    repository = FakeUserRepository()
    uow = FakeUnitOfWork(repository)
    handler = UserExistsHandler(uow=uow)

    result = handler.handle(UserExistsQuery(user_id=UserId.generate()))

    assert result.success is True
    assert result.value is False
    assert result.errors == ()


@pytest.mark.unit
def test_a_repository_get_failure_is_reported_as_a_failed_result() -> None:
    repository = FakeUserRepository(fail_on_get=True)
    uow = FakeUnitOfWork(repository)
    handler = UserExistsHandler(uow=uow)

    result = handler.handle(UserExistsQuery(user_id=UserId.generate()))

    assert result.success is False
    assert result.errors
