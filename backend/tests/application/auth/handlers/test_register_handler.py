"""Tests for app/application/auth/handlers/register_handler.py."""

import pytest

from app.application.auth.commands.register import RegisterCommand
from app.application.auth.handlers.register_handler import RegisterHandler
from app.domain.auth.credential import Credential
from app.domain.auth.events import CredentialRegistered
from app.domain.auth.value_objects import Email
from app.domain.user.events import UserRegistered
from app.domain.user.identifiers import UserId
from app.domain.user.value_objects import Locale, Timezone
from tests.application.auth.factories import (
    FakeCredentialRepository,
    FakePasswordHasher,
    FakeTokenService,
    FakeUnitOfWork,
    OrderTrackingDispatcher,
    OrderTrackingUnitOfWork,
    RecordingDispatcher,
    a_fixed_clock,
    a_registered_credential,
)
from tests.application.user.factories import FakeUserRepository

_A_COMMAND = RegisterCommand(
    email=Email("sai@example.com"),
    password="correct horse battery staple",
    locale=Locale("en"),
    timezone=Timezone("UTC"),
)


def _a_handler(
    *,
    user_repository: FakeUserRepository | None = None,
    credential_repository: FakeCredentialRepository | None = None,
    dispatcher: RecordingDispatcher | None = None,
    fail_on_commit: bool = False,
) -> tuple[RegisterHandler, FakeUnitOfWork, RecordingDispatcher, FakeTokenService]:
    uow = FakeUnitOfWork(
        user_repository=user_repository or FakeUserRepository(),
        credential_repository=credential_repository or FakeCredentialRepository(),
        fail_on_commit=fail_on_commit,
    )
    dispatcher = dispatcher or RecordingDispatcher()
    token_service = FakeTokenService()
    handler = RegisterHandler(
        uow=uow,
        dispatcher=dispatcher,
        clock=a_fixed_clock(),
        password_hasher=FakePasswordHasher(),
        token_service=token_service,
    )
    return handler, uow, dispatcher, token_service


@pytest.mark.unit
def test_registers_a_user_and_credential_and_returns_tokens() -> None:
    user_repository = FakeUserRepository()
    credential_repository = FakeCredentialRepository()
    handler, _, _, _ = _a_handler(
        user_repository=user_repository, credential_repository=credential_repository
    )

    result = handler.handle(_A_COMMAND)

    assert result.success is True
    assert result.value is not None
    assert result.value.token_type == "bearer"
    assert result.value.expires_in == 900
    assert len(user_repository.added) == 1
    assert len(credential_repository.added) == 1


@pytest.mark.unit
def test_the_new_user_and_credential_share_the_same_id() -> None:
    user_repository = FakeUserRepository()
    credential_repository = FakeCredentialRepository()
    handler, _, _, _ = _a_handler(
        user_repository=user_repository, credential_repository=credential_repository
    )

    handler.handle(_A_COMMAND)

    assert user_repository.added[0].id == credential_repository.added[0].id


@pytest.mark.unit
def test_hashes_the_password_rather_than_storing_it_raw() -> None:
    credential_repository = FakeCredentialRepository()
    handler, _, _, _ = _a_handler(credential_repository=credential_repository)

    handler.handle(_A_COMMAND)

    stored = credential_repository.added[0]
    assert stored.password_hash.value != _A_COMMAND.password


@pytest.mark.unit
def test_rejects_an_already_registered_email() -> None:
    existing_id = UserId.generate()
    existing = a_registered_credential(user_id=existing_id, email="sai@example.com")
    credential_repository = FakeCredentialRepository({existing_id: existing})
    handler, uow, dispatcher, _ = _a_handler(credential_repository=credential_repository)

    result = handler.handle(_A_COMMAND)

    assert result.success is False
    assert "already registered" in result.errors[0]
    assert uow.rolled_back is True
    assert uow.committed is False
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_dispatches_both_registered_events_after_commit() -> None:
    handler, _, dispatcher, _ = _a_handler()

    handler.handle(_A_COMMAND)

    kinds = {type(event) for event in dispatcher.dispatched}
    assert kinds == {UserRegistered, CredentialRegistered}


@pytest.mark.unit
def test_dispatch_happens_strictly_after_commit() -> None:
    call_order: list[str] = []
    uow = OrderTrackingUnitOfWork(
        call_order,
        user_repository=FakeUserRepository(),
        credential_repository=FakeCredentialRepository(),
    )
    dispatcher = OrderTrackingDispatcher(call_order)
    handler = RegisterHandler(
        uow=uow,
        dispatcher=dispatcher,
        clock=a_fixed_clock(),
        password_hasher=FakePasswordHasher(),
        token_service=FakeTokenService(),
    )

    handler.handle(_A_COMMAND)

    assert call_order == ["commit", "dispatch"]


@pytest.mark.unit
def test_a_commit_failure_is_reported_and_rolls_back() -> None:
    handler, uow, dispatcher, _ = _a_handler(fail_on_commit=True)

    result = handler.handle(_A_COMMAND)

    assert result.success is False
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_generates_distinct_users_each_call() -> None:
    handler, _, _, _ = _a_handler()

    first = handler.handle(
        RegisterCommand(
            email=Email("one@example.com"),
            password="correct horse battery staple",
            locale=Locale("en"),
            timezone=Timezone("UTC"),
        )
    )
    second = handler.handle(
        RegisterCommand(
            email=Email("two@example.com"),
            password="correct horse battery staple",
            locale=Locale("en"),
            timezone=Timezone("UTC"),
        )
    )

    assert first.success is True
    assert second.success is True
    assert first.value is not None and second.value is not None


@pytest.mark.unit
def test_issues_tokens_for_the_new_credential() -> None:
    handler, _, _, token_service = _a_handler()

    result = handler.handle(_A_COMMAND)

    assert result.value is not None
    assert len(token_service.issued_access_tokens) == 1
    assert len(token_service.issued_refresh_tokens) == 1
    _, token_version = token_service.issued_refresh_tokens[0]
    assert token_version == 0


@pytest.mark.unit
def test_new_credential_starts_at_token_version_zero() -> None:
    credential_repository = FakeCredentialRepository()
    handler, _, _, _ = _a_handler(credential_repository=credential_repository)

    handler.handle(_A_COMMAND)

    stored: Credential = credential_repository.added[0]
    assert stored.token_version == 0
