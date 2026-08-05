"""Tests for app/application/auth/handlers/logout_handler.py."""

import pytest

from app.application.auth.commands.logout import LogoutCommand
from app.application.auth.handlers.logout_handler import LogoutHandler
from app.domain.auth.events import TokensRevoked
from app.domain.user.identifiers import UserId
from tests.application.auth.factories import (
    FakeCredentialRepository,
    FakeUnitOfWork,
    OrderTrackingDispatcher,
    OrderTrackingUnitOfWork,
    RecordingDispatcher,
    a_fixed_clock,
    a_registered_credential,
)


@pytest.mark.unit
def test_revokes_the_credentials_tokens() -> None:
    user_id = UserId.generate()
    credential = a_registered_credential(user_id=user_id)
    repository = FakeCredentialRepository({user_id: credential})
    uow = FakeUnitOfWork(credential_repository=repository)
    handler = LogoutHandler(uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock())

    result = handler.handle(LogoutCommand(user_id=user_id))

    assert result.success is True
    assert credential.token_version == 1


@pytest.mark.unit
def test_dispatches_a_tokens_revoked_event_after_commit() -> None:
    user_id = UserId.generate()
    credential = a_registered_credential(user_id=user_id)
    credential.pull_domain_events()  # drain CredentialRegistered from setup
    repository = FakeCredentialRepository({user_id: credential})
    uow = FakeUnitOfWork(credential_repository=repository)
    dispatcher = RecordingDispatcher()
    handler = LogoutHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    handler.handle(LogoutCommand(user_id=user_id))

    assert len(dispatcher.dispatched) == 1
    assert isinstance(dispatcher.dispatched[0], TokensRevoked)


@pytest.mark.unit
def test_dispatch_happens_strictly_after_commit() -> None:
    user_id = UserId.generate()
    credential = a_registered_credential(user_id=user_id)
    repository = FakeCredentialRepository({user_id: credential})
    call_order: list[str] = []
    uow = OrderTrackingUnitOfWork(call_order, credential_repository=repository)
    dispatcher = OrderTrackingDispatcher(call_order)
    handler = LogoutHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    handler.handle(LogoutCommand(user_id=user_id))

    assert call_order == ["commit", "dispatch"]


@pytest.mark.unit
def test_fails_when_the_credential_does_not_exist() -> None:
    repository = FakeCredentialRepository()
    uow = FakeUnitOfWork(credential_repository=repository)
    dispatcher = RecordingDispatcher()
    handler = LogoutHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(LogoutCommand(user_id=UserId.generate()))

    assert result.success is False
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []
