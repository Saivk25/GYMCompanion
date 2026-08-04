"""Tests for app/application/readiness/queries/get_readiness.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.application.readiness.queries.get_readiness import GetReadinessQuery
from app.application.shared.query import Query
from app.domain.readiness.identifiers import ReadinessId


@pytest.mark.unit
def test_get_readiness_query_is_a_query() -> None:
    assert isinstance(GetReadinessQuery(readiness_id=ReadinessId.generate()), Query)


@pytest.mark.unit
def test_get_readiness_query_exposes_its_readiness_id() -> None:
    readiness_id = ReadinessId.generate()
    query = GetReadinessQuery(readiness_id=readiness_id)
    assert query.readiness_id == readiness_id


@pytest.mark.unit
def test_get_readiness_query_is_immutable() -> None:
    query = GetReadinessQuery(readiness_id=ReadinessId.generate())
    with pytest.raises(FrozenInstanceError):
        query.readiness_id = ReadinessId.generate()  # type: ignore[misc]
