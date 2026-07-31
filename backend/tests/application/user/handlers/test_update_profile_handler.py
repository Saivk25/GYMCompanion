"""Tests for app/application/user/handlers/update_profile_handler.py."""

import pytest

from app.application.user.commands.update_profile import UpdateProfileCommand
from app.application.user.handlers.update_profile_handler import UpdateProfileHandler
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.user.enums import ExperienceLevel
from app.domain.user.events import UserProfileUpdated
from app.domain.user.identifiers import UserId
from app.domain.user.user import User
from app.domain.user.value_objects import AuthMethod, Locale, Timezone, UserProfile
from tests.application.user.factories import (
    FakeUnitOfWork,
    FakeUserRepository,
    OrderTrackingDispatcher,
    OrderTrackingUnitOfWork,
    RecordingDispatcher,
    a_fixed_clock,
)

_A_PROFILE = UserProfile(
    height_cm=178.0, birth_year=1998, experience_level=ExperienceLevel.BEGINNER
)


def _a_registered_user() -> User:
    user = User.register(
        user_id=UserId.generate(),
        locale=Locale("en"),
        timezone=Timezone("UTC"),
        auth_method=AuthMethod("webauthn_passkey"),
        clock=a_fixed_clock(),
    )
    user.pull_domain_events()  # drain UserRegistered from setup
    return user


@pytest.mark.unit
def test_replaces_the_profile_and_returns_the_user_id() -> None:
    user = _a_registered_user()
    repository = FakeUserRepository({user.id: user})
    uow = FakeUnitOfWork(repository)
    handler = UpdateProfileHandler(uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock())

    result = handler.handle(UpdateProfileCommand(user_id=user.id, profile=_A_PROFILE))

    assert result.success is True
    assert result.value == user.id
    assert user.profile == _A_PROFILE


@pytest.mark.unit
def test_commits_and_dispatches_the_profile_updated_event() -> None:
    user = _a_registered_user()
    repository = FakeUserRepository({user.id: user})
    uow = FakeUnitOfWork(repository)
    dispatcher = RecordingDispatcher()
    handler = UpdateProfileHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    handler.handle(UpdateProfileCommand(user_id=user.id, profile=_A_PROFILE))

    assert uow.committed is True
    assert len(dispatcher.dispatched) == 1
    assert isinstance(dispatcher.dispatched[0], UserProfileUpdated)
    assert dispatcher.dispatched[0].profile == _A_PROFILE


@pytest.mark.unit
def test_dispatch_happens_strictly_after_commit() -> None:
    user = _a_registered_user()
    call_order: list[str] = []
    repository = FakeUserRepository({user.id: user})
    uow = OrderTrackingUnitOfWork(repository, call_order)
    dispatcher = OrderTrackingDispatcher(call_order)
    handler = UpdateProfileHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    handler.handle(UpdateProfileCommand(user_id=user.id, profile=_A_PROFILE))

    assert call_order == ["commit", "dispatch"]


@pytest.mark.unit
def test_a_missing_user_is_reported_as_a_failed_result_and_rolls_back() -> None:
    repository = FakeUserRepository()
    uow = FakeUnitOfWork(repository)
    dispatcher = RecordingDispatcher()
    handler = UpdateProfileHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())
    missing_id = UserId.generate()

    result = handler.handle(UpdateProfileCommand(user_id=missing_id, profile=_A_PROFILE))

    assert result.success is False
    assert str(missing_id) in result.errors[0]
    assert uow.rolled_back is True
    assert uow.committed is False
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_repository_get_failure_is_reported_as_a_failed_result_and_rolls_back() -> None:
    repository = FakeUserRepository(fail_on_get=True)
    uow = FakeUnitOfWork(repository)
    dispatcher = RecordingDispatcher()
    handler = UpdateProfileHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(UpdateProfileCommand(user_id=UserId.generate(), profile=_A_PROFILE))

    assert result.success is False
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_commit_failure_is_reported_as_a_failed_result_and_rolls_back() -> None:
    user = _a_registered_user()
    repository = FakeUserRepository({user.id: user})
    uow = FakeUnitOfWork(repository, fail_on_commit=True)
    dispatcher = RecordingDispatcher()
    handler = UpdateProfileHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(UpdateProfileCommand(user_id=user.id, profile=_A_PROFILE))

    assert result.success is False
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_domain_invariant_violation_propagates_and_still_rolls_back() -> None:
    """`update_profile()` is rejected on a deleted user
    (`DomainInvariantViolationError`) — this handler never converts
    that into a failed `ApplicationResult`; it always propagates, per
    `docs/adr/0023-user-application-use-cases.md`."""
    user = _a_registered_user()
    user.delete()
    repository = FakeUserRepository({user.id: user})
    uow = FakeUnitOfWork(repository)
    dispatcher = RecordingDispatcher()
    handler = UpdateProfileHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    with pytest.raises(DomainInvariantViolationError, match="cannot modify a user"):
        handler.handle(UpdateProfileCommand(user_id=user.id, profile=_A_PROFILE))

    assert uow.rolled_back is True
    assert uow.committed is False
    assert dispatcher.dispatched == []
