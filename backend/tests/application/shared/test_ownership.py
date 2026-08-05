"""Tests for app/application/shared/ownership.py."""

import pytest

from app.application.shared.ownership import ensure_owner
from app.domain.user.identifiers import UserId


@pytest.mark.unit
def test_returns_none_when_the_requester_is_the_owner() -> None:
    user_id = UserId.generate()

    denial = ensure_owner(owner_id=user_id, requester_id=user_id)

    assert denial is None


@pytest.mark.unit
def test_returns_a_denial_message_when_the_requester_is_not_the_owner() -> None:
    owner_id = UserId.generate()
    requester_id = UserId.generate()

    denial = ensure_owner(owner_id=owner_id, requester_id=requester_id)

    assert denial is not None
    assert isinstance(denial, str)
    assert "permission" in denial.lower()
