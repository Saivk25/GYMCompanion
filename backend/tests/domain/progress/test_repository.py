"""Tests for app/domain/progress/repository.py.

Mirrors `tests/domain/workout/test_repository.py`'s shape — see that
file's docstring for why the behavior under test is really the shared
kernel's `Repository` abstractness (plus this module's own
`list_by_user()` extension), exercised here through the concrete
`ProgressRepository`/`Progress` pairing.
"""

import pytest

from app.domain.progress.identifiers import ProgressId
from app.domain.progress.progress import Progress
from app.domain.progress.repository import ProgressRepository
from app.domain.user.identifiers import UserId
from tests.domain.progress.factories import a_recorded_progress


class _InMemoryProgressRepository(ProgressRepository):
    def __init__(self) -> None:
        self._records: dict[ProgressId, Progress] = {}

    def get(self, entity_id: ProgressId) -> Progress | None:
        return self._records.get(entity_id)

    def add(self, aggregate: Progress) -> None:
        self._records[aggregate.id] = aggregate

    def remove(self, aggregate: Progress) -> None:
        del self._records[aggregate.id]

    def list_by_user(self, user_id: UserId) -> list[Progress]:
        return [record for record in self._records.values() if record.user_id == user_id]


@pytest.mark.unit
def test_progress_repository_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        ProgressRepository()  # type: ignore[abstract]


@pytest.mark.unit
def test_a_subclass_missing_list_by_user_still_cannot_be_instantiated() -> None:
    class _IncompleteProgressRepository(ProgressRepository):
        def get(self, entity_id: ProgressId) -> Progress | None:
            return None

        def add(self, aggregate: Progress) -> None:
            pass

        def remove(self, aggregate: Progress) -> None:
            pass

        # list_by_user() deliberately not implemented

    with pytest.raises(TypeError):
        _IncompleteProgressRepository()  # type: ignore[abstract]


@pytest.mark.unit
def test_a_complete_in_memory_implementation_is_usable() -> None:
    repo = _InMemoryProgressRepository()
    progress = a_recorded_progress()

    assert repo.get(progress.id) is None

    repo.add(progress)
    assert repo.get(progress.id) == progress

    repo.remove(progress)
    assert repo.get(progress.id) is None


@pytest.mark.unit
def test_list_by_user_returns_only_that_users_records() -> None:
    repo = _InMemoryProgressRepository()
    user_id = UserId.generate()
    mine_first = a_recorded_progress(user_id=user_id)
    mine_second = a_recorded_progress(user_id=user_id)
    someone_elses = a_recorded_progress()
    repo.add(mine_first)
    repo.add(mine_second)
    repo.add(someone_elses)

    result = repo.list_by_user(user_id)

    assert set(result) == {mine_first, mine_second}


@pytest.mark.unit
def test_list_by_user_returns_empty_for_a_user_with_no_records() -> None:
    repo = _InMemoryProgressRepository()
    assert repo.list_by_user(UserId.generate()) == []
