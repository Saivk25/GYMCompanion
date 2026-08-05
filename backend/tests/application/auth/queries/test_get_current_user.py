"""Tests for app/application/auth/queries/get_current_user.py."""

import pytest

from app.application.auth.queries.get_current_user import GetCurrentUserQuery
from app.domain.user.identifiers import UserId


@pytest.mark.unit
def test_carries_the_user_id() -> None:
    user_id = UserId.generate()
    query = GetCurrentUserQuery(user_id=user_id)
    assert query.user_id == user_id
