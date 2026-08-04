"""Tests for app/application/readiness/queries/list_readiness.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.application.readiness.queries.list_readiness import ListReadinessQuery
from app.application.shared.query import Query
from app.domain.user.identifiers import UserId


@pytest.mark.unit
def test_list_readiness_query_is_a_query() -> None:
    assert isinstance(ListReadinessQuery(user_id=UserId.generate()), Query)


@pytest.mark.unit
def test_list_readiness_query_exposes_its_user_id() -> None:
    user_id = UserId.generate()
    query = ListReadinessQuery(user_id=user_id)
    assert query.user_id == user_id


@pytest.mark.unit
def test_list_readiness_query_is_immutable() -> None:
    query = ListReadinessQuery(user_id=UserId.generate())
    with pytest.raises(FrozenInstanceError):
        query.user_id = UserId.generate()  # type: ignore[misc]
