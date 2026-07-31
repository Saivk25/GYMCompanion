"""Tests for app/application/user/handlers/update_preferences_handler.py."""

import pytest

from app.application.user.commands.update_preferences import UpdatePreferencesCommand
from app.application.user.handlers.update_preferences_handler import UpdatePreferencesHandler
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.user.identifiers import UserId
from app.domain.user.user import User
from app.domain.user.value_objects import AuthMethod, Locale, Timezone, UserPreferences
from tests.application.user.factories import (
    FakeUnitOfWork,
    FakeUserRepository,
    OrderTrackingDispatcher,
    OrderTrackingUnitOfWork,
    RecordingDispatcher,
    a_fixed_clock,
)

_NEW_PREFERENCES = UserPreferences(biometric_app_lock_enabled=True)


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
def test_replaces_preferences_and_returns_the_user_id() -> None:
    user = _a_registered_user()
    repository = FakeUserRepository({user.id: user})
    uow = FakeUnitOfWork(repository)
    handler = UpdatePreferencesHandler(uow=uow, dispatcher=RecordingDispatcher())

    result = handler.handle(UpdatePreferencesCommand(user_id=user.id, preferences=_NEW_PREFERENCES))

    assert result.success is True
    assert result.value == user.id
    assert user.preferences == _NEW_PREFERENCES


@pytest.mark.unit
def test_commits_and_dispatches_no_events_since_none_are_raised() -> None:
    """`User.update_preferences()` raises no event — see its own
    docstring — so a successful update still calls `dispatch()`, just
    with an empty sequence, matching `DomainEventDispatcher.dispatch`'s
    own "dispatching an empty sequence... does nothing" contract."""
    user = _a_registered_user()
    repository = FakeUserRepository({user.id: user})
    uow = FakeUnitOfWork(repository)
    dispatcher = RecordingDispatcher()
    handler = UpdatePreferencesHandler(uow=uow, dispatcher=dispatcher)

    handler.handle(UpdatePreferencesCommand(user_id=user.id, preferences=_NEW_PREFERENCES))

    assert uow.committed is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_dispatch_happens_strictly_after_commit() -> None:
    user = _a_registered_user()
    call_order: list[str] = []
    repository = FakeUserRepository({user.id: user})
    uow = OrderTrackingUnitOfWork(repository, call_order)
    dispatcher = OrderTrackingDispatcher(call_order)
    handler = UpdatePreferencesHandler(uow=uow, dispatcher=dispatcher)

    handler.handle(UpdatePreferencesCommand(user_id=user.id, preferences=_NEW_PREFERENCES))

    assert call_order == ["commit", "dispatch"]


@pytest.mark.unit
def test_a_missing_user_is_reported_as_a_failed_result_and_rolls_back() -> None:
    repository = FakeUserRepository()
    uow = FakeUnitOfWork(repository)
    dispatcher = RecordingDispatcher()
    handler = UpdatePreferencesHandler(uow=uow, dispatcher=dispatcher)
    missing_id = UserId.generate()

    result = handler.handle(
        UpdatePreferencesCommand(user_id=missing_id, preferences=_NEW_PREFERENCES)
    )

    assert result.success is False
    assert str(missing_id) in result.errors[0]
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_repository_get_failure_is_reported_as_a_failed_result_and_rolls_back() -> None:
    repository = FakeUserRepository(fail_on_get=True)
    uow = FakeUnitOfWork(repository)
    dispatcher = RecordingDispatcher()
    handler = UpdatePreferencesHandler(uow=uow, dispatcher=dispatcher)

    result = handler.handle(
        UpdatePreferencesCommand(user_id=UserId.generate(), preferences=_NEW_PREFERENCES)
    )

    assert result.success is False
    assert uow.rolled_back is True


@pytest.mark.unit
def test_a_commit_failure_is_reported_as_a_failed_result_and_rolls_back() -> None:
    user = _a_registered_user()
    repository = FakeUserRepository({user.id: user})
    uow = FakeUnitOfWork(repository, fail_on_commit=True)
    dispatcher = RecordingDispatcher()
    handler = UpdatePreferencesHandler(uow=uow, dispatcher=dispatcher)

    result = handler.handle(UpdatePreferencesCommand(user_id=user.id, preferences=_NEW_PREFERENCES))

    assert result.success is False
    assert uow.rolled_back is True


@pytest.mark.unit
def test_a_domain_invariant_violation_propagates_and_still_rolls_back() -> None:
    user = _a_registered_user()
    user.delete()
    repository = FakeUserRepository({user.id: user})
    uow = FakeUnitOfWork(repository)
    dispatcher = RecordingDispatcher()
    handler = UpdatePreferencesHandler(uow=uow, dispatcher=dispatcher)

    with pytest.raises(DomainInvariantViolationError, match="cannot modify a user"):
        handler.handle(UpdatePreferencesCommand(user_id=user.id, preferences=_NEW_PREFERENCES))

    assert uow.rolled_back is True
    assert dispatcher.dispatched == []
