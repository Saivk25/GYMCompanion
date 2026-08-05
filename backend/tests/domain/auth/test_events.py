"""Tests for app/domain/auth/events.py.

Immutability, `event_id` auto-generation, and `occurred_at` timezone
enforcement are `DomainEvent` base behavior, already fully covered by
`tests/domain/shared_kernel/test_events.py`. This file only proves each
Credential-specific event carries the fields it's supposed to.
"""

from datetime import datetime, timezone

import pytest

from app.domain.auth.events import CredentialRegistered, TokensRevoked
from app.domain.user.identifiers import UserId


@pytest.mark.unit
def test_credential_registered_carries_user_id_and_email() -> None:
    user_id = UserId.generate()
    event = CredentialRegistered(
        occurred_at=datetime.now(timezone.utc), user_id=user_id, email="sai@example.com"
    )
    assert event.user_id == user_id
    assert event.email == "sai@example.com"


@pytest.mark.unit
def test_tokens_revoked_carries_user_id() -> None:
    user_id = UserId.generate()
    event = TokensRevoked(occurred_at=datetime.now(timezone.utc), user_id=user_id)
    assert event.user_id == user_id
