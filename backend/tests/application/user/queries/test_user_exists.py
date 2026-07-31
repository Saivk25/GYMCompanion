"""Tests for app/application/user/queries/user_exists.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.application.shared.query import Query
from app.application.user.queries.user_exists import UserExistsQuery
from app.domain.user.identifiers import UserId


@pytest.mark.unit
def test_user_exists_query_is_a_query() -> None:
    assert isinstance(UserExistsQuery(user_id=UserId.generate()), Query)


@pytest.mark.unit
def test_user_exists_query_exposes_its_field() -> None:
    user_id = UserId.generate()
    query = UserExistsQuery(user_id=user_id)
    assert query.user_id == user_id


@pytest.mark.unit
def test_user_exists_query_is_immutable() -> None:
    query = UserExistsQuery(user_id=UserId.generate())
    with pytest.raises(FrozenInstanceError):
        query.user_id = UserId.generate()  # type: ignore[misc]
