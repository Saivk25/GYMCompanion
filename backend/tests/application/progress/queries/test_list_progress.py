"""Tests for app/application/progress/queries/list_progress.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.application.progress.queries.list_progress import ListProgressQuery
from app.application.shared.query import Query
from app.domain.user.identifiers import UserId


@pytest.mark.unit
def test_list_progress_query_is_a_query() -> None:
    assert isinstance(ListProgressQuery(user_id=UserId.generate()), Query)


@pytest.mark.unit
def test_list_progress_query_exposes_its_user_id() -> None:
    user_id = UserId.generate()
    query = ListProgressQuery(user_id=user_id)
    assert query.user_id == user_id


@pytest.mark.unit
def test_list_progress_query_is_immutable() -> None:
    query = ListProgressQuery(user_id=UserId.generate())
    with pytest.raises(FrozenInstanceError):
        query.user_id = UserId.generate()  # type: ignore[misc]
