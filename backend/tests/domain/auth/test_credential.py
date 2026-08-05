"""Tests for app/domain/auth/credential.py."""

from datetime import datetime, timezone

import pytest

from app.domain.auth.credential import Credential
from app.domain.auth.enums import Permission, Role
from app.domain.auth.events import CredentialRegistered, TokensRevoked
from app.domain.auth.value_objects import Email, PasswordHash
from app.domain.shared_kernel.clock import Clock
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.user.identifiers import UserId
from tests.domain.auth.factories import a_fixed_clock


def _a_registered_credential(
    *, clock: Clock | None = None, user_id: UserId | None = None
) -> Credential:
    return Credential.register(
        user_id=user_id or UserId.generate(),
        email=Email("sai@example.com"),
        password_hash=PasswordHash("$2b$12$abcdefghijklmnopqrstuv"),
        clock=clock or a_fixed_clock(),
    )


# --- register() ---


@pytest.mark.unit
def test_register_exposes_the_fields_it_was_given() -> None:
    user_id = UserId.generate()
    credential = _a_registered_credential(user_id=user_id)
    assert credential.id == user_id
    assert credential.email == Email("sai@example.com")
    assert credential.password_hash == PasswordHash("$2b$12$abcdefghijklmnopqrstuv")


@pytest.mark.unit
def test_register_starts_as_member_with_token_version_zero() -> None:
    credential = _a_registered_credential()
    assert credential.role == Role.MEMBER
    assert credential.token_version == 0


@pytest.mark.unit
def test_register_stamps_created_at_from_the_clock() -> None:
    clock = a_fixed_clock()
    credential = _a_registered_credential(clock=clock)
    assert credential.created_at == clock.now()


@pytest.mark.unit
def test_register_records_a_credential_registered_event() -> None:
    clock = a_fixed_clock()
    user_id = UserId.generate()
    credential = Credential.register(
        user_id=user_id,
        email=Email("sai@example.com"),
        password_hash=PasswordHash("$2b$12$abcdefghijklmnopqrstuv"),
        clock=clock,
    )

    events = credential.pull_domain_events()

    assert len(events) == 1
    assert isinstance(events[0], CredentialRegistered)
    assert events[0].user_id == user_id
    assert events[0].email == "sai@example.com"
    assert events[0].occurred_at == clock.now()


# --- revoke_tokens() ---


@pytest.mark.unit
def test_revoke_tokens_advances_token_version() -> None:
    credential = _a_registered_credential()
    credential.revoke_tokens(clock=a_fixed_clock())
    assert credential.token_version == 1


@pytest.mark.unit
def test_revoke_tokens_is_cumulative_across_calls() -> None:
    credential = _a_registered_credential()
    credential.revoke_tokens(clock=a_fixed_clock())
    credential.revoke_tokens(clock=a_fixed_clock())
    assert credential.token_version == 2


@pytest.mark.unit
def test_revoke_tokens_records_a_tokens_revoked_event() -> None:
    credential = _a_registered_credential()
    credential.pull_domain_events()  # drain CredentialRegistered from setup
    clock = a_fixed_clock()

    credential.revoke_tokens(clock=clock)

    events = credential.pull_domain_events()
    assert len(events) == 1
    assert isinstance(events[0], TokensRevoked)
    assert events[0].user_id == credential.id
    assert events[0].occurred_at == clock.now()


# --- has_permission() ---


@pytest.mark.unit
def test_member_has_manage_own_data_permission() -> None:
    credential = _a_registered_credential()
    assert credential.has_permission(Permission.MANAGE_OWN_DATA) is True


# --- __init__ construction (repository rehydration path) ---


@pytest.mark.unit
def test_constructor_rejects_a_naive_created_at() -> None:
    with pytest.raises(DomainInvariantViolationError, match="timezone-aware"):
        Credential(
            UserId.generate(),
            email=Email("sai@example.com"),
            password_hash=PasswordHash("$2b$12$abcdefghijklmnopqrstuv"),
            created_at=datetime(2026, 1, 1),  # deliberately naive
        )


@pytest.mark.unit
def test_constructor_rejects_a_negative_token_version() -> None:
    with pytest.raises(DomainInvariantViolationError, match="token_version"):
        Credential(
            UserId.generate(),
            email=Email("sai@example.com"),
            password_hash=PasswordHash("$2b$12$abcdefghijklmnopqrstuv"),
            token_version=-1,
            created_at=datetime.now(timezone.utc),
        )


@pytest.mark.unit
def test_constructor_rehydrates_an_existing_credential_without_raising_an_event() -> None:
    """The path a repository uses to reconstruct a Credential already in
    storage — re-raising CredentialRegistered here would be wrong."""
    credential = Credential(
        UserId.generate(),
        email=Email("sai@example.com"),
        password_hash=PasswordHash("$2b$12$abcdefghijklmnopqrstuv"),
        role=Role.MEMBER,
        token_version=3,
        created_at=datetime.now(timezone.utc),
    )
    assert credential.pull_domain_events() == []
    assert credential.token_version == 3


@pytest.mark.unit
def test_register_generates_distinct_credentials_for_distinct_users() -> None:
    assert _a_registered_credential().id != _a_registered_credential().id
