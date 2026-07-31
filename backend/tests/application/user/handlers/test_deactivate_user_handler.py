"""Tests for app/application/user/handlers/deactivate_user_handler.py."""

import pytest

from app.application.user.commands.deactivate_user import DeactivateUserCommand
from app.application.user.handlers.deactivate_user_handler import DeactivateUserHandler
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.user.enums import AccountStatus
from app.domain.user.identifiers import UserId
from app.domain.user.user import User
from app.domain.user.value_objects import AuthMethod, Locale, Timezone
from tests.application.user.factories import (
    FakeUnitOfWork,
    FakeUserRepository,
    OrderTrackingDispatcher,
    OrderTrackingUnitOfWork,
    RecordingDispatcher,
    a_fixed_clock,
)


def _an_active_user() -> User:
    user = User.register(
        user_id=UserId.generate(),
        locale=Locale("en"),
        timezone=Timezone("UTC"),
        auth_method=AuthMethod("webauthn_passkey"),
        clock=a_fixed_clock(),
    )
    user.activate()
    user.pull_domain_events()
    return user


@pytest.mark.unit
def test_suspends_the_user_and_returns_its_id() -> None:
    user = _an_active_user()
    repository = FakeUserRepository({user.id: user})
    uow = FakeUnitOfWork(repository)
    handler = DeactivateUserHandler(uow=uow, dispatcher=RecordingDispatcher())

    result = handler.handle(DeactivateUserCommand(user_id=user.id))

    assert result.success is True
    assert result.value == user.id
    assert user.account_status == AccountStatus.SUSPENDED


@pytest.mark.unit
def test_commits_and_dispatches_no_events_since_none_are_raised() -> None:
    user = _an_active_user()
    repository = FakeUserRepository({user.id: user})
    uow = FakeUnitOfWork(repository)
    dispatcher = RecordingDispatcher()
    handler = DeactivateUserHandler(uow=uow, dispatcher=dispatcher)

    handler.handle(DeactivateUserCommand(user_id=user.id))

    assert uow.committed is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_dispatch_happens_strictly_after_commit() -> None:
    user = _an_active_user()
    call_order: list[str] = []
    repository = FakeUserRepository({user.id: user})
    uow = OrderTrackingUnitOfWork(repository, call_order)
    dispatcher = OrderTrackingDispatcher(call_order)
    handler = DeactivateUserHandler(uow=uow, dispatcher=dispatcher)

    handler.handle(DeactivateUserCommand(user_id=user.id))

    assert call_order == ["commit", "dispatch"]


@pytest.mark.unit
def test_a_missing_user_is_reported_as_a_failed_result_and_rolls_back() -> None:
    repository = FakeUserRepository()
    uow = FakeUnitOfWork(repository)
    dispatcher = RecordingDispatcher()
    handler = DeactivateUserHandler(uow=uow, dispatcher=dispatcher)
    missing_id = UserId.generate()

    result = handler.handle(DeactivateUserCommand(user_id=missing_id))

    assert result.success is False
    assert str(missing_id) in result.errors[0]
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_repository_get_failure_is_reported_as_a_failed_result_and_rolls_back() -> None:
    repository = FakeUserRepository(fail_on_get=True)
    uow = FakeUnitOfWork(repository)
    dispatcher = RecordingDispatcher()
    handler = DeactivateUserHandler(uow=uow, dispatcher=dispatcher)

    result = handler.handle(DeactivateUserCommand(user_id=UserId.generate()))

    assert result.success is False
    assert uow.rolled_back is True


@pytest.mark.unit
def test_a_commit_failure_is_reported_as_a_failed_result_and_rolls_back() -> None:
    user = _an_active_user()
    repository = FakeUserRepository({user.id: user})
    uow = FakeUnitOfWork(repository, fail_on_commit=True)
    dispatcher = RecordingDispatcher()
    handler = DeactivateUserHandler(uow=uow, dispatcher=dispatcher)

    result = handler.handle(DeactivateUserCommand(user_id=user.id))

    assert result.success is False
    assert uow.rolled_back is True


@pytest.mark.unit
def test_a_domain_invariant_violation_propagates_and_still_rolls_back() -> None:
    """`suspend()` is only legal from Active — a still-Invited user
    (never activated) raises `DomainInvariantViolationError`, which
    this handler always lets propagate."""
    user = User.register(
        user_id=UserId.generate(),
        locale=Locale("en"),
        timezone=Timezone("UTC"),
        auth_method=AuthMethod("webauthn_passkey"),
        clock=a_fixed_clock(),
    )
    user.pull_domain_events()
    repository = FakeUserRepository({user.id: user})
    uow = FakeUnitOfWork(repository)
    dispatcher = RecordingDispatcher()
    handler = DeactivateUserHandler(uow=uow, dispatcher=dispatcher)

    with pytest.raises(DomainInvariantViolationError, match="cannot transition"):
        handler.handle(DeactivateUserCommand(user_id=user.id))

    assert uow.rolled_back is True
    assert dispatcher.dispatched == []
