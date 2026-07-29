"""Tests for app/domain/nutrition/identifiers.py.

Deliberately thin — see `tests/domain/user/test_identifiers.py`'s
docstring for why: `NutritionId`'s generic identifier behavior is the
shared kernel's own `EntityId` behavior, already fully covered by
`tests/domain/shared_kernel/test_identifiers.py`.
"""

import pytest

from app.domain.nutrition.identifiers import NutritionId
from app.domain.shared_kernel.identifiers import EntityId


@pytest.mark.unit
def test_nutrition_id_is_an_entity_id() -> None:
    assert issubclass(NutritionId, EntityId)


@pytest.mark.unit
def test_generate_returns_a_nutrition_id() -> None:
    assert isinstance(NutritionId.generate(), NutritionId)


@pytest.mark.unit
def test_parse_round_trips_through_str() -> None:
    original = NutritionId.generate()
    assert NutritionId.parse(str(original)) == original
