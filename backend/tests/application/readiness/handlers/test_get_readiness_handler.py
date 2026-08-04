"""Tests for app/application/readiness/handlers/get_readiness_handler.py."""

import pytest

from app.application.readiness.handlers.get_readiness_handler import GetReadinessHandler
from app.application.readiness.queries.get_readiness import GetReadinessQuery
from app.domain.readiness.identifiers import ReadinessId
from tests.application.readiness.factories import (
    FakeReadinessRepository,
    FakeUnitOfWork,
    a_recorded_readiness,
)


@pytest.mark.unit
def test_returns_a_readiness_dto_for_an_existing_check_in() -> None:
    readiness = a_recorded_readiness()
    uow = FakeUnitOfWork(entries=FakeReadinessRepository({readiness.id: readiness}))
    handler = GetReadinessHandler(uow=uow)

    result = handler.handle(GetReadinessQuery(readiness_id=readiness.id))

    assert result.success is True
    assert result.value is not None
    assert result.value.readiness_id == readiness.id
    assert result.value.user_id == readiness.user_id


@pytest.mark.unit
def test_a_missing_readiness_check_in_is_reported_as_a_failed_result() -> None:
    uow = FakeUnitOfWork()
    handler = GetReadinessHandler(uow=uow)
    missing_id = ReadinessId.generate()

    result = handler.handle(GetReadinessQuery(readiness_id=missing_id))

    assert result.success is False
    assert str(missing_id) in result.errors[0]


@pytest.mark.unit
def test_never_commits_since_nothing_was_staged() -> None:
    readiness = a_recorded_readiness()
    uow = FakeUnitOfWork(entries=FakeReadinessRepository({readiness.id: readiness}))
    handler = GetReadinessHandler(uow=uow)

    handler.handle(GetReadinessQuery(readiness_id=readiness.id))

    assert uow.committed is False


@pytest.mark.unit
def test_a_repository_get_failure_is_reported_as_a_failed_result() -> None:
    uow = FakeUnitOfWork(entries=FakeReadinessRepository(fail_on_get=True))
    handler = GetReadinessHandler(uow=uow)

    result = handler.handle(GetReadinessQuery(readiness_id=ReadinessId.generate()))

    assert result.success is False
