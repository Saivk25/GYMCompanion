"""Tests for app/application/user/queries/get_user.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.application.shared.query import Query
from app.application.user.queries.get_user import GetUserQuery
from app.domain.user.identifiers import UserId


@pytest.mark.unit
def test_get_user_query_is_a_query() -> None:
    assert isinstance(GetUserQuery(user_id=UserId.generate()), Query)


@pytest.mark.unit
def test_get_user_query_exposes_its_field() -> None:
    user_id = UserId.generate()
    query = GetUserQuery(user_id=user_id)
    assert query.user_id == user_id


@pytest.mark.unit
def test_get_user_query_is_immutable() -> None:
    query = GetUserQuery(user_id=UserId.generate())
    with pytest.raises(FrozenInstanceError):
        query.user_id = UserId.generate()  # type: ignore[misc]
