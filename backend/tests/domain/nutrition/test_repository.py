"""Tests for app/domain/nutrition/repository.py.

Mirrors `tests/domain/progress/test_repository.py`'s shape — see that
file's docstring for why the behavior under test is really the shared
kernel's `Repository` abstractness, exercised here through the concrete
`NutritionRepository`/`Nutrition` pairing.
"""

import pytest

from app.domain.nutrition.identifiers import NutritionId
from app.domain.nutrition.nutrition import Nutrition
from app.domain.nutrition.repository import NutritionRepository
from tests.domain.nutrition.factories import a_recorded_nutrition


@pytest.mark.unit
def test_nutrition_repository_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        NutritionRepository()  # type: ignore[abstract]


@pytest.mark.unit
def test_a_complete_in_memory_implementation_is_usable() -> None:
    class _InMemoryNutritionRepository(NutritionRepository):
        def __init__(self) -> None:
            self._records: dict[NutritionId, Nutrition] = {}

        def get(self, entity_id: NutritionId) -> Nutrition | None:
            return self._records.get(entity_id)

        def add(self, aggregate: Nutrition) -> None:
            self._records[aggregate.id] = aggregate

        def remove(self, aggregate: Nutrition) -> None:
            del self._records[aggregate.id]

    repo = _InMemoryNutritionRepository()
    nutrition = a_recorded_nutrition()

    assert repo.get(nutrition.id) is None

    repo.add(nutrition)
    assert repo.get(nutrition.id) == nutrition

    repo.remove(nutrition)
    assert repo.get(nutrition.id) is None
