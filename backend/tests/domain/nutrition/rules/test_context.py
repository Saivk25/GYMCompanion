"""Tests for app/domain/nutrition/rules/context.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.domain.nutrition.rules.context import NutritionRuleContext
from app.domain.nutrition.value_objects import Calories, Protein
from app.domain.rules.context import RuleContext
from tests.domain.nutrition.factories import a_fixed_clock, a_recorded_nutrition


@pytest.mark.unit
def test_is_a_rule_context() -> None:
    assert isinstance(NutritionRuleContext(), RuleContext)


@pytest.mark.unit
def test_defaults_every_field_to_none() -> None:
    context = NutritionRuleContext()
    assert context.calories is None
    assert context.protein is None
    assert context.carbohydrates is None
    assert context.fat is None
    assert context.fiber is None
    assert context.water_intake is None


@pytest.mark.unit
def test_accepts_every_field_explicitly() -> None:
    context = NutritionRuleContext(calories=Calories(2000.0), protein=Protein(120.0))
    assert context.calories == Calories(2000.0)
    assert context.protein == Protein(120.0)


@pytest.mark.unit
def test_is_immutable() -> None:
    context = NutritionRuleContext()
    with pytest.raises(FrozenInstanceError):
        context.protein = Protein(100.0)  # type: ignore[misc]


# --- from_nutrition() ---


@pytest.mark.unit
def test_from_nutrition_maps_only_the_six_rule_relevant_fields() -> None:
    nutrition = a_recorded_nutrition()
    nutrition.update_nutrition(
        calories=Calories(2200.0), protein=Protein(130.0), clock=a_fixed_clock()
    )

    context = NutritionRuleContext.from_nutrition(nutrition)

    assert context.calories == nutrition.calories
    assert context.protein == nutrition.protein
    assert context.carbohydrates == nutrition.carbohydrates
    assert context.fat == nutrition.fat
    assert context.fiber == nutrition.fiber
    assert context.water_intake == nutrition.water_intake


@pytest.mark.unit
def test_from_nutrition_with_no_optional_fields_recorded() -> None:
    nutrition = a_recorded_nutrition()
    context = NutritionRuleContext.from_nutrition(nutrition)
    assert context.calories is None
    assert context.protein is None
    assert context.carbohydrates is None
    assert context.fat is None
    assert context.fiber is None
    assert context.water_intake is None


@pytest.mark.unit
def test_from_nutrition_does_not_reflect_later_mutations() -> None:
    nutrition = a_recorded_nutrition()
    context = NutritionRuleContext.from_nutrition(nutrition)

    nutrition.update_nutrition(protein=Protein(150.0), clock=a_fixed_clock())

    assert context.protein is None
    assert nutrition.protein == Protein(150.0)


@pytest.mark.unit
def test_from_nutrition_ignores_sugar() -> None:
    """`NutritionRuleContext` deliberately has no `sugar` field — no
    `SugarRule` is one of the six rules this phase implements."""
    assert not hasattr(NutritionRuleContext(), "sugar")
