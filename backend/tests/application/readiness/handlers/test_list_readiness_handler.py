"""Tests for
app/application/readiness/handlers/list_readiness_handler.py."""

import pytest

from app.application.readiness.handlers.list_readiness_handler import ListReadinessHandler
from app.application.readiness.queries.list_readiness import ListReadinessQuery
from app.domain.user.identifiers import UserId
from tests.application.readiness.factories import (
    FakeReadinessRepository,
    FakeUnitOfWork,
    a_recorded_readiness,
)


@pytest.mark.unit
def test_returns_every_check_in_for_the_user_as_dtos() -> None:
    user_id = UserId.generate()
    mine_first = a_recorded_readiness(user_id=user_id)
    mine_second = a_recorded_readiness(user_id=user_id)
    someone_elses = a_recorded_readiness()
    uow = FakeUnitOfWork(
        entries=FakeReadinessRepository(
            {
                mine_first.id: mine_first,
                mine_second.id: mine_second,
                someone_elses.id: someone_elses,
            }
        )
    )
    handler = ListReadinessHandler(uow=uow)

    result = handler.handle(ListReadinessQuery(user_id=user_id))

    assert result.success is True
    assert result.value is not None
    returned_ids = {dto.readiness_id for dto in result.value}
    assert returned_ids == {mine_first.id, mine_second.id}


@pytest.mark.unit
def test_returns_an_empty_tuple_for_a_user_with_no_check_ins() -> None:
    uow = FakeUnitOfWork()
    handler = ListReadinessHandler(uow=uow)

    result = handler.handle(ListReadinessQuery(user_id=UserId.generate()))

    assert result.success is True
    assert result.value == ()


@pytest.mark.unit
def test_never_commits_since_nothing_was_staged() -> None:
    uow = FakeUnitOfWork()
    handler = ListReadinessHandler(uow=uow)

    handler.handle(ListReadinessQuery(user_id=UserId.generate()))

    assert uow.committed is False


@pytest.mark.unit
def test_a_repository_list_failure_is_reported_as_a_failed_result() -> None:
    uow = FakeUnitOfWork(entries=FakeReadinessRepository(fail_on_list=True))
    handler = ListReadinessHandler(uow=uow)

    result = handler.handle(ListReadinessQuery(user_id=UserId.generate()))

    assert result.success is False
