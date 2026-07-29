"""Tests for app/domain/progress/repository.py.

Mirrors `tests/domain/exercise/test_repository.py`'s shape — see that
file's docstring for why the behavior under test is really the shared
kernel's `Repository` abstractness, exercised here through the concrete
`ProgressRepository`/`Progress` pairing.
"""

import pytest

from app.domain.progress.identifiers import ProgressId
from app.domain.progress.progress import Progress
from app.domain.progress.repository import ProgressRepository
from tests.domain.progress.factories import a_recorded_progress


@pytest.mark.unit
def test_progress_repository_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        ProgressRepository()  # type: ignore[abstract]


@pytest.mark.unit
def test_a_complete_in_memory_implementation_is_usable() -> None:
    class _InMemoryProgressRepository(ProgressRepository):
        def __init__(self) -> None:
            self._records: dict[ProgressId, Progress] = {}

        def get(self, entity_id: ProgressId) -> Progress | None:
            return self._records.get(entity_id)

        def add(self, aggregate: Progress) -> None:
            self._records[aggregate.id] = aggregate

        def remove(self, aggregate: Progress) -> None:
            del self._records[aggregate.id]

    repo = _InMemoryProgressRepository()
    progress = a_recorded_progress()

    assert repo.get(progress.id) is None

    repo.add(progress)
    assert repo.get(progress.id) == progress

    repo.remove(progress)
    assert repo.get(progress.id) is None
