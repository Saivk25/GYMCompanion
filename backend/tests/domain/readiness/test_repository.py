"""Tests for app/domain/readiness/repository.py.

Mirrors `tests/domain/nutrition/test_repository.py`'s shape — see that
file's docstring for why the behavior under test is really the shared
kernel's `Repository` abstractness (plus this module's own
`list_by_user()` extension), exercised here through the concrete
`ReadinessRepository`/`Readiness` pairing.
"""

import pytest

from app.domain.readiness.identifiers import ReadinessId
from app.domain.readiness.readiness import Readiness
from app.domain.readiness.repository import ReadinessRepository
from app.domain.user.identifiers import UserId
from tests.domain.readiness.factories import a_recorded_readiness


class _InMemoryReadinessRepository(ReadinessRepository):
    def __init__(self) -> None:
        self._records: dict[ReadinessId, Readiness] = {}

    def get(self, entity_id: ReadinessId) -> Readiness | None:
        return self._records.get(entity_id)

    def add(self, aggregate: Readiness) -> None:
        self._records[aggregate.id] = aggregate

    def remove(self, aggregate: Readiness) -> None:
        del self._records[aggregate.id]

    def list_by_user(self, user_id: UserId) -> list[Readiness]:
        return [record for record in self._records.values() if record.user_id == user_id]


@pytest.mark.unit
def test_readiness_repository_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        ReadinessRepository()  # type: ignore[abstract]


@pytest.mark.unit
def test_a_subclass_missing_list_by_user_still_cannot_be_instantiated() -> None:
    class _IncompleteReadinessRepository(ReadinessRepository):
        def get(self, entity_id: ReadinessId) -> Readiness | None:
            return None

        def add(self, aggregate: Readiness) -> None:
            pass

        def remove(self, aggregate: Readiness) -> None:
            pass

        # list_by_user() deliberately not implemented

    with pytest.raises(TypeError):
        _IncompleteReadinessRepository()  # type: ignore[abstract]


@pytest.mark.unit
def test_a_complete_in_memory_implementation_is_usable() -> None:
    repo = _InMemoryReadinessRepository()
    readiness = a_recorded_readiness()

    assert repo.get(readiness.id) is None

    repo.add(readiness)
    assert repo.get(readiness.id) == readiness

    repo.remove(readiness)
    assert repo.get(readiness.id) is None


@pytest.mark.unit
def test_list_by_user_returns_only_that_users_check_ins() -> None:
    repo = _InMemoryReadinessRepository()
    user_id = UserId.generate()
    mine_first = a_recorded_readiness(user_id=user_id)
    mine_second = a_recorded_readiness(user_id=user_id)
    someone_elses = a_recorded_readiness()
    repo.add(mine_first)
    repo.add(mine_second)
    repo.add(someone_elses)

    result = repo.list_by_user(user_id)

    assert set(result) == {mine_first, mine_second}


@pytest.mark.unit
def test_list_by_user_returns_empty_for_a_user_with_no_check_ins() -> None:
    repo = _InMemoryReadinessRepository()
    assert repo.list_by_user(UserId.generate()) == []
