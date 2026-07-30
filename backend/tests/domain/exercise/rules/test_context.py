"""Tests for app/domain/exercise/rules/context.py."""

import pytest

from app.domain.exercise.rules.context import ExerciseRecommendationRuleContext
from app.domain.rules.context import RuleContext
from tests.domain.exercise.rules.factories import an_exercise_context


@pytest.mark.unit
def test_is_a_rule_context() -> None:
    context = ExerciseRecommendationRuleContext(exercise=an_exercise_context())
    assert isinstance(context, RuleContext)


@pytest.mark.unit
def test_defaults_every_optional_field_to_none_or_empty() -> None:
    context = ExerciseRecommendationRuleContext(exercise=an_exercise_context())
    assert context.goal is None
    assert context.safety_result is None
    assert context.readiness_result is None
    assert context.progressive_overload is None
    assert context.declared_restrictions == ()
    assert context.available_equipment is None
    assert context.recent_movement_patterns == ()


@pytest.mark.unit
def test_is_immutable() -> None:
    context = ExerciseRecommendationRuleContext(exercise=an_exercise_context())
    with pytest.raises(AttributeError):
        context.goal = None  # type: ignore[misc]
