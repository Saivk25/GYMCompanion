"""Tests for app/domain/readiness/repository.py.

Mirrors `tests/domain/progress/test_repository.py`'s shape — see that
file's docstring for why the behavior under test is really the shared
kernel's `Repository` abstractness, exercised here through the concrete
`ReadinessRepository`/`Readiness` pairing.
"""

import pytest

from app.domain.readiness.identifiers import ReadinessId
from app.domain.readiness.readiness import Readiness
from app.domain.readiness.repository import ReadinessRepository
from tests.domain.readiness.factories import a_recorded_readiness


@pytest.mark.unit
def test_readiness_repository_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        ReadinessRepository()  # type: ignore[abstract]


@pytest.mark.unit
def test_a_complete_in_memory_implementation_is_usable() -> None:
    class _InMemoryReadinessRepository(ReadinessRepository):
        def __init__(self) -> None:
            self._records: dict[ReadinessId, Readiness] = {}

        def get(self, entity_id: ReadinessId) -> Readiness | None:
            return self._records.get(entity_id)

        def add(self, aggregate: Readiness) -> None:
            self._records[aggregate.id] = aggregate

        def remove(self, aggregate: Readiness) -> None:
            del self._records[aggregate.id]

    repo = _InMemoryReadinessRepository()
    readiness = a_recorded_readiness()

    assert repo.get(readiness.id) is None

    repo.add(readiness)
    assert repo.get(readiness.id) == readiness

    repo.remove(readiness)
    assert repo.get(readiness.id) is None
