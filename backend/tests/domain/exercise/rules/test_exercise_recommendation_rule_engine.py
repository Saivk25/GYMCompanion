"""Tests for app/domain/exercise/rules/exercise_recommendation_rule_engine.py."""

import pytest

from app.domain.exercise.rules.contraindicated_exercise_rule import ContraindicatedExerciseRule
from app.domain.exercise.rules.equipment_rule import EquipmentRule
from app.domain.exercise.rules.exercise_recommendation_rule_engine import (
    ExerciseRecommendationRuleEngine,
)
from app.domain.exercise.rules.exercise_selection_rule import ExerciseSelectionRule
from app.domain.exercise.rules.movement_balance_rule import MovementBalanceRule
from app.domain.exercise.rules.progression_stage_rule import ProgressionStageRule
from app.domain.exercise.value_objects import Contraindications, EquipmentRequirement
from app.domain.rules.engine import RuleEngine
from app.domain.rules.result import RuleId
from app.domain.rules.severity import RecommendationSeverity
from tests.domain.exercise.rules.factories import (
    DeclaredRestriction,
    a_recommendation_context,
    a_rule_result,
    an_exercise_context,
)


@pytest.mark.unit
def test_is_a_rule_engine() -> None:
    assert isinstance(ExerciseRecommendationRuleEngine(), RuleEngine)


@pytest.mark.unit
def test_default_construction_registers_all_five_rules() -> None:
    engine = ExerciseRecommendationRuleEngine()
    rule_types = {type(rule) for rule in engine.rules}
    expected_rule_types: set[type[object]] = {
        ExerciseSelectionRule,
        ContraindicatedExerciseRule,
        MovementBalanceRule,
        EquipmentRule,
        ProgressionStageRule,
    }
    assert rule_types == expected_rule_types
    assert len(engine.rules) == 5


@pytest.mark.unit
def test_accepts_a_custom_rule_set() -> None:
    custom_rule = ExerciseSelectionRule(rule_id=RuleId("custom.selection"))
    engine = ExerciseRecommendationRuleEngine([custom_rule])
    assert engine.rules == (custom_rule,)


# --- evaluate(): a fully compatible candidate ---


@pytest.mark.unit
def test_evaluating_a_bare_context_passes() -> None:
    result = ExerciseRecommendationRuleEngine().evaluate(a_recommendation_context())
    assert result.passed is True
    assert result.triggered_rules == ()


# --- evaluate(): a hard-excluded candidate ---


@pytest.mark.unit
def test_evaluating_a_contraindicated_and_equipment_incompatible_candidate_fails_both() -> None:
    exercise = an_exercise_context(
        contraindications=Contraindications(frozenset({"shoulder_pain"})),
        equipment_requirements=frozenset({EquipmentRequirement("barbell")}),
    )
    context = a_recommendation_context(
        exercise=exercise,
        declared_restrictions=(DeclaredRestriction(tag="shoulder_pain"),),
        available_equipment=frozenset(),
    )

    result = ExerciseRecommendationRuleEngine().evaluate(context)

    assert result.passed is False
    assert RuleId("exercise_recommendation.contraindicated_exercise") in result.triggered_rules
    assert RuleId("exercise_recommendation.equipment") in result.triggered_rules
    assert result.severity == RecommendationSeverity.WARNING


# --- evaluate(): a soft-biased but not excluded candidate ---


@pytest.mark.unit
def test_evaluating_a_readiness_biased_candidate_still_passes_with_recommendations() -> None:
    readiness_result = a_rule_result(passed=False)
    context = a_recommendation_context(readiness_result=readiness_result)

    result = ExerciseRecommendationRuleEngine().evaluate(context)

    assert result.passed is True
    assert result.triggered_rules == ()
    assert len(result.recommendations) >= 1


# --- determinism / side-effect freedom ---


@pytest.mark.unit
def test_evaluate_is_deterministic() -> None:
    exercise = an_exercise_context(
        contraindications=Contraindications(frozenset({"shoulder_pain"}))
    )
    context = a_recommendation_context(
        exercise=exercise, declared_restrictions=(DeclaredRestriction(tag="shoulder_pain"),)
    )
    engine = ExerciseRecommendationRuleEngine()
    assert engine.evaluate(context) == engine.evaluate(context)


@pytest.mark.unit
def test_evaluate_does_not_mutate_the_context() -> None:
    restrictions = (DeclaredRestriction(tag="shoulder_pain"),)
    context = a_recommendation_context(declared_restrictions=restrictions)
    ExerciseRecommendationRuleEngine().evaluate(context)
    assert context.declared_restrictions == restrictions
