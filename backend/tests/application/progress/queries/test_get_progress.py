"""Tests for app/application/progress/queries/get_progress.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.application.progress.queries.get_progress import GetProgressQuery
from app.application.shared.query import Query
from app.domain.progress.identifiers import ProgressId
from app.domain.user.identifiers import UserId


@pytest.mark.unit
def test_get_progress_query_is_a_query() -> None:
    assert isinstance(
        GetProgressQuery(progress_id=ProgressId.generate(), requester_id=UserId.generate()), Query
    )


@pytest.mark.unit
def test_get_progress_query_exposes_its_progress_id() -> None:
    progress_id = ProgressId.generate()
    query = GetProgressQuery(progress_id=progress_id, requester_id=UserId.generate())
    assert query.progress_id == progress_id


@pytest.mark.unit
def test_get_progress_query_is_immutable() -> None:
    query = GetProgressQuery(progress_id=ProgressId.generate(), requester_id=UserId.generate())
    with pytest.raises(FrozenInstanceError):
        query.progress_id = ProgressId.generate()  # type: ignore[misc]
