"""Tests for app/application/progress/handlers/get_progress_handler.py."""

import pytest

from app.application.progress.handlers.get_progress_handler import GetProgressHandler
from app.application.progress.queries.get_progress import GetProgressQuery
from app.domain.progress.identifiers import ProgressId
from app.domain.user.identifiers import UserId
from tests.application.progress.factories import (
    FakeProgressRepository,
    FakeUnitOfWork,
    a_recorded_progress,
)


@pytest.mark.unit
def test_returns_a_progress_dto_for_an_existing_record() -> None:
    progress = a_recorded_progress()
    uow = FakeUnitOfWork(records=FakeProgressRepository({progress.id: progress}))
    handler = GetProgressHandler(uow=uow)

    result = handler.handle(
        GetProgressQuery(progress_id=progress.id, requester_id=progress.user_id)
    )

    assert result.success is True
    assert result.value is not None
    assert result.value.progress_id == progress.id
    assert result.value.user_id == progress.user_id


@pytest.mark.unit
def test_a_missing_progress_record_is_reported_as_a_failed_result() -> None:
    uow = FakeUnitOfWork()
    handler = GetProgressHandler(uow=uow)
    missing_id = ProgressId.generate()

    result = handler.handle(
        GetProgressQuery(progress_id=missing_id, requester_id=UserId.generate())
    )

    assert result.success is False
    assert str(missing_id) in result.errors[0]


@pytest.mark.unit
def test_never_commits_since_nothing_was_staged() -> None:
    progress = a_recorded_progress()
    uow = FakeUnitOfWork(records=FakeProgressRepository({progress.id: progress}))
    handler = GetProgressHandler(uow=uow)

    handler.handle(GetProgressQuery(progress_id=progress.id, requester_id=progress.user_id))

    assert uow.committed is False


@pytest.mark.unit
def test_a_repository_get_failure_is_reported_as_a_failed_result() -> None:
    uow = FakeUnitOfWork(records=FakeProgressRepository(fail_on_get=True))
    handler = GetProgressHandler(uow=uow)

    result = handler.handle(
        GetProgressQuery(progress_id=ProgressId.generate(), requester_id=UserId.generate())
    )

    assert result.success is False


@pytest.mark.unit
def test_a_non_owner_requester_is_denied() -> None:
    progress = a_recorded_progress()
    uow = FakeUnitOfWork(records=FakeProgressRepository({progress.id: progress}))
    handler = GetProgressHandler(uow=uow)

    result = handler.handle(
        GetProgressQuery(progress_id=progress.id, requester_id=UserId.generate())
    )

    assert result.success is False
    assert result.forbidden is True
    assert result.value is None
