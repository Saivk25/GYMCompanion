"""Tests for app/domain/exercise/rules/equipment_rule.py."""

import pytest

from app.domain.exercise.rules.equipment_rule import EquipmentRule
from app.domain.exercise.value_objects import EquipmentRequirement
from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity
from tests.domain.exercise.rules.factories import a_recommendation_context, an_exercise_context

# --- identity ---


@pytest.mark.unit
def test_default_identity() -> None:
    rule = EquipmentRule()
    assert rule.id == RuleId("exercise_recommendation.equipment")
    assert rule.name == "Equipment"
    assert rule.severity == RecommendationSeverity.WARNING


# --- missing data ---


@pytest.mark.unit
def test_passes_when_no_equipment_availability_supplied() -> None:
    rule = EquipmentRule()
    exercise = an_exercise_context(
        equipment_requirements=frozenset({EquipmentRequirement("barbell")})
    )
    context = a_recommendation_context(exercise=exercise)
    result = rule.evaluate(context)
    assert result.passed is True
    assert "cannot evaluate" in result.explanation.lower()


# --- compatibility ---


@pytest.mark.unit
def test_passes_for_a_bodyweight_exercise() -> None:
    rule = EquipmentRule()
    exercise = an_exercise_context(equipment_requirements=frozenset())
    context = a_recommendation_context(exercise=exercise, available_equipment=frozenset())
    result = rule.evaluate(context)
    assert result.passed is True


@pytest.mark.unit
def test_passes_when_all_required_equipment_is_available() -> None:
    rule = EquipmentRule()
    exercise = an_exercise_context(
        equipment_requirements=frozenset({EquipmentRequirement("barbell")})
    )
    context = a_recommendation_context(
        exercise=exercise,
        available_equipment=frozenset(
            {EquipmentRequirement("barbell"), EquipmentRequirement("bench")}
        ),
    )
    result = rule.evaluate(context)
    assert result.passed is True


@pytest.mark.unit
def test_fails_when_required_equipment_is_missing() -> None:
    rule = EquipmentRule()
    exercise = an_exercise_context(
        equipment_requirements=frozenset(
            {EquipmentRequirement("barbell"), EquipmentRequirement("squat rack")}
        )
    )
    context = a_recommendation_context(
        exercise=exercise, available_equipment=frozenset({EquipmentRequirement("barbell")})
    )
    result = rule.evaluate(context)
    assert result.passed is False
    assert result.triggered_rules == (RuleId("exercise_recommendation.equipment"),)
    assert "squat rack" in result.explanation
    assert len(result.recommendations) == 1


# --- determinism ---


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    rule = EquipmentRule()
    exercise = an_exercise_context(
        equipment_requirements=frozenset({EquipmentRequirement("barbell")})
    )
    context = a_recommendation_context(exercise=exercise, available_equipment=frozenset())
    assert rule.evaluate(context) == rule.evaluate(context)
