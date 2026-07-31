"""Tests for app/application/user/handlers/create_user_handler.py."""

import pytest

from app.application.user.commands.create_user import CreateUserCommand
from app.application.user.handlers.create_user_handler import CreateUserHandler
from app.domain.user.events import UserRegistered
from app.domain.user.value_objects import AuthMethod, Locale, Timezone
from tests.application.user.factories import (
    FakeUnitOfWork,
    FakeUserRepository,
    OrderTrackingDispatcher,
    OrderTrackingUnitOfWork,
    RecordingDispatcher,
    a_fixed_clock,
)

_A_COMMAND = CreateUserCommand(
    locale=Locale("en"), timezone=Timezone("UTC"), auth_method=AuthMethod("webauthn_passkey")
)


@pytest.mark.unit
def test_registers_a_new_user_and_returns_its_id() -> None:
    repository = FakeUserRepository()
    uow = FakeUnitOfWork(repository)
    dispatcher = RecordingDispatcher()
    handler = CreateUserHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(_A_COMMAND)

    assert result.success is True
    assert result.value is not None
    assert repository.get(result.value) is not None
    assert repository.get(result.value).locale == Locale("en")  # type: ignore[union-attr]


@pytest.mark.unit
def test_commits_the_unit_of_work() -> None:
    repository = FakeUserRepository()
    uow = FakeUnitOfWork(repository)
    handler = CreateUserHandler(uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock())

    handler.handle(_A_COMMAND)

    assert uow.committed is True
    assert uow.rolled_back is False


@pytest.mark.unit
def test_dispatches_the_user_registered_event_after_commit() -> None:
    repository = FakeUserRepository()
    uow = FakeUnitOfWork(repository)
    dispatcher = RecordingDispatcher()
    handler = CreateUserHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(_A_COMMAND)

    assert len(dispatcher.dispatched) == 1
    event = dispatcher.dispatched[0]
    assert isinstance(event, UserRegistered)
    assert event.user_id == result.value
    assert event.locale == Locale("en")


@pytest.mark.unit
def test_dispatch_happens_strictly_after_commit() -> None:
    """Event dispatch ordering: never before a successful commit — see
    `app.domain.shared_kernel.aggregate_root`'s own "persist first,
    publish after" contract."""
    call_order: list[str] = []
    repository = FakeUserRepository()
    uow = OrderTrackingUnitOfWork(repository, call_order)
    dispatcher = OrderTrackingDispatcher(call_order)
    handler = CreateUserHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    handler.handle(_A_COMMAND)

    assert call_order == ["commit", "dispatch"]


@pytest.mark.unit
def test_a_repository_add_failure_is_reported_as_a_failed_result() -> None:
    """Simulates a duplicate-user scenario: the repository's `add()`
    rejects the new aggregate (e.g. an id collision a concrete
    implementation's unique constraint would catch)."""
    repository = FakeUserRepository(fail_on_add=True)
    uow = FakeUnitOfWork(repository)
    dispatcher = RecordingDispatcher()
    handler = CreateUserHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(_A_COMMAND)

    assert result.success is False
    assert result.errors
    assert "already exists" in result.errors[0]


@pytest.mark.unit
def test_a_repository_add_failure_rolls_back_and_never_dispatches() -> None:
    repository = FakeUserRepository(fail_on_add=True)
    uow = FakeUnitOfWork(repository)
    dispatcher = RecordingDispatcher()
    handler = CreateUserHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    handler.handle(_A_COMMAND)

    assert uow.rolled_back is True
    assert uow.committed is False
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_commit_failure_is_reported_as_a_failed_result_and_rolls_back() -> None:
    repository = FakeUserRepository()
    uow = FakeUnitOfWork(repository, fail_on_commit=True)
    dispatcher = RecordingDispatcher()
    handler = CreateUserHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(_A_COMMAND)

    assert result.success is False
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_generates_a_distinct_user_each_call() -> None:
    repository = FakeUserRepository()
    uow = FakeUnitOfWork(repository)
    handler = CreateUserHandler(uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock())

    first = handler.handle(_A_COMMAND)
    second = handler.handle(_A_COMMAND)

    assert first.value != second.value
