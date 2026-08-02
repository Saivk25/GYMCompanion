"""Tests for app/application/progress/handlers/list_progress_handler.py."""

import pytest

from app.application.progress.handlers.list_progress_handler import ListProgressHandler
from app.application.progress.queries.list_progress import ListProgressQuery
from app.domain.user.identifiers import UserId
from tests.application.progress.factories import (
    FakeProgressRepository,
    FakeUnitOfWork,
    a_recorded_progress,
)


@pytest.mark.unit
def test_returns_every_record_for_the_user_as_dtos() -> None:
    user_id = UserId.generate()
    mine_first = a_recorded_progress(user_id=user_id)
    mine_second = a_recorded_progress(user_id=user_id)
    someone_elses = a_recorded_progress()
    uow = FakeUnitOfWork(
        records=FakeProgressRepository(
            {
                mine_first.id: mine_first,
                mine_second.id: mine_second,
                someone_elses.id: someone_elses,
            }
        )
    )
    handler = ListProgressHandler(uow=uow)

    result = handler.handle(ListProgressQuery(user_id=user_id))

    assert result.success is True
    assert result.value is not None
    returned_ids = {dto.progress_id for dto in result.value}
    assert returned_ids == {mine_first.id, mine_second.id}


@pytest.mark.unit
def test_returns_an_empty_tuple_for_a_user_with_no_records() -> None:
    uow = FakeUnitOfWork()
    handler = ListProgressHandler(uow=uow)

    result = handler.handle(ListProgressQuery(user_id=UserId.generate()))

    assert result.success is True
    assert result.value == ()


@pytest.mark.unit
def test_never_commits_since_nothing_was_staged() -> None:
    uow = FakeUnitOfWork()
    handler = ListProgressHandler(uow=uow)

    handler.handle(ListProgressQuery(user_id=UserId.generate()))

    assert uow.committed is False


@pytest.mark.unit
def test_a_repository_list_failure_is_reported_as_a_failed_result() -> None:
    uow = FakeUnitOfWork(records=FakeProgressRepository(fail_on_list=True))
    handler = ListProgressHandler(uow=uow)

    result = handler.handle(ListProgressQuery(user_id=UserId.generate()))

    assert result.success is False
