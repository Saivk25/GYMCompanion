"""Tests for app/domain/nutrition/repository.py.

Mirrors `tests/domain/workout/test_repository.py`'s shape — see that
file's docstring for why the behavior under test is really the shared
kernel's `Repository` abstractness (plus this module's own
`list_by_user()` extension), exercised here through the concrete
`NutritionRepository`/`Nutrition` pairing.
"""

import pytest

from app.domain.nutrition.identifiers import NutritionId
from app.domain.nutrition.nutrition import Nutrition
from app.domain.nutrition.repository import NutritionRepository
from app.domain.user.identifiers import UserId
from tests.domain.nutrition.factories import a_recorded_nutrition


class _InMemoryNutritionRepository(NutritionRepository):
    def __init__(self) -> None:
        self._records: dict[NutritionId, Nutrition] = {}

    def get(self, entity_id: NutritionId) -> Nutrition | None:
        return self._records.get(entity_id)

    def add(self, aggregate: Nutrition) -> None:
        self._records[aggregate.id] = aggregate

    def remove(self, aggregate: Nutrition) -> None:
        del self._records[aggregate.id]

    def list_by_user(self, user_id: UserId) -> list[Nutrition]:
        return [record for record in self._records.values() if record.user_id == user_id]


@pytest.mark.unit
def test_nutrition_repository_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        NutritionRepository()  # type: ignore[abstract]


@pytest.mark.unit
def test_a_subclass_missing_list_by_user_still_cannot_be_instantiated() -> None:
    class _IncompleteNutritionRepository(NutritionRepository):
        def get(self, entity_id: NutritionId) -> Nutrition | None:
            return None

        def add(self, aggregate: Nutrition) -> None:
            pass

        def remove(self, aggregate: Nutrition) -> None:
            pass

        # list_by_user() deliberately not implemented

    with pytest.raises(TypeError):
        _IncompleteNutritionRepository()  # type: ignore[abstract]


@pytest.mark.unit
def test_a_complete_in_memory_implementation_is_usable() -> None:
    repo = _InMemoryNutritionRepository()
    nutrition = a_recorded_nutrition()

    assert repo.get(nutrition.id) is None

    repo.add(nutrition)
    assert repo.get(nutrition.id) == nutrition

    repo.remove(nutrition)
    assert repo.get(nutrition.id) is None


@pytest.mark.unit
def test_list_by_user_returns_only_that_users_entries() -> None:
    repo = _InMemoryNutritionRepository()
    user_id = UserId.generate()
    mine_first = a_recorded_nutrition(user_id=user_id)
    mine_second = a_recorded_nutrition(user_id=user_id)
    someone_elses = a_recorded_nutrition()
    repo.add(mine_first)
    repo.add(mine_second)
    repo.add(someone_elses)

    result = repo.list_by_user(user_id)

    assert set(result) == {mine_first, mine_second}


@pytest.mark.unit
def test_list_by_user_returns_empty_for_a_user_with_no_entries() -> None:
    repo = _InMemoryNutritionRepository()
    assert repo.list_by_user(UserId.generate()) == []
