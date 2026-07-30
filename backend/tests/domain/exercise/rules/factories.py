"""Shared test helpers for the Exercise Recommendation Rule Engine's
test suite.

Not itself a test file (no `test_` prefix, so pytest never collects it) —
mirrors `tests/domain/safety/rules/factories.py`'s reasoning exactly.
"""

from __future__ import annotations

from app.domain.exercise.context import ExerciseContext
from app.domain.exercise.enums import Difficulty, ExerciseStatus, MovementPattern
from app.domain.exercise.identifiers import ExerciseId
from app.domain.exercise.rules.context import ExerciseRecommendationRuleContext
from app.domain.exercise.value_objects import (
    Contraindications,
    EquipmentRequirement,
    ExerciseName,
    PrimaryMuscle,
    SecondaryMuscles,
)
from app.domain.goal.context import GoalContext
from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.severity import RecommendationSeverity
from app.domain.safety.rules.context import DeclaredRestriction
from app.domain.workout.rules.context import ProgressiveOverloadRuleContext

# Re-exported so a single import in a test module reaches both this
# package's own helpers and the ones it builds on.
from tests.domain.goal.rules.factories import a_goal_context
from tests.domain.workout.rules.factories import a_context as a_progressive_overload_context
from tests.domain.workout.rules.factories import a_summary

__all__ = [
    "DeclaredRestriction",
    "a_goal_context",
    "a_progressive_overload_context",
    "a_recommendation_context",
    "a_rule_result",
    "a_summary",
    "an_exercise_context",
]


def an_exercise_context(
    *,
    exercise_id: ExerciseId | None = None,
    status: ExerciseStatus = ExerciseStatus.ACTIVE,
    name: ExerciseName | None = None,
    movement_pattern: MovementPattern = MovementPattern.PUSH,
    difficulty: Difficulty = Difficulty.BEGINNER,
    primary_muscles: tuple[PrimaryMuscle, ...] = (),
    secondary_muscles: SecondaryMuscles | None = None,
    equipment_requirements: frozenset[EquipmentRequirement] = frozenset(),
    contraindications: Contraindications | None = None,
) -> ExerciseContext:
    """An `ExerciseContext` built directly (not via a live `Exercise`
    aggregate) — every field this package's rules read is directly
    overridable, the same reasoning `tests/domain/goal/rules/factories.py`'s
    `a_goal_context()` documents."""
    return ExerciseContext(
        exercise_id=exercise_id or ExerciseId.generate(),
        status=status,
        name=name or ExerciseName("Barbell Bench Press"),
        movement_pattern=movement_pattern,
        difficulty=difficulty,
        primary_muscles=primary_muscles,
        secondary_muscles=secondary_muscles or SecondaryMuscles(),
        equipment_requirements=equipment_requirements,
        contraindications=contraindications or Contraindications(),
    )


def a_rule_result(
    *,
    passed: bool = True,
    severity: RecommendationSeverity = RecommendationSeverity.INFO,
    explanation: str = "ok",
    recommendations: tuple[Recommendation, ...] = (),
    triggered_rules: tuple[RuleId, ...] = (),
) -> RuleResult:
    """A `RuleResult` built directly — standing in for whatever a real
    `SafetyRuleEngine`/Readiness rule engine would have already
    computed, per this package's own "compose outputs, don't
    re-derive them" discipline."""
    return RuleResult(
        passed=passed,
        severity=severity,
        explanation=explanation,
        recommendations=recommendations,
        triggered_rules=triggered_rules,
    )


def a_recommendation_context(
    *,
    exercise: ExerciseContext | None = None,
    goal: GoalContext | None = None,
    safety_result: RuleResult | None = None,
    readiness_result: RuleResult | None = None,
    progressive_overload: ProgressiveOverloadRuleContext | None = None,
    declared_restrictions: tuple[DeclaredRestriction, ...] = (),
    available_equipment: frozenset[EquipmentRequirement] | None = None,
    recent_movement_patterns: tuple[MovementPattern, ...] = (),
) -> ExerciseRecommendationRuleContext:
    """An `ExerciseRecommendationRuleContext` wrapping the given fields
    as-is — every field defaults to "nothing supplied", matching
    `ExerciseRecommendationRuleContext`'s own field defaults, except
    `exercise`, which is required upstream and defaults to
    `an_exercise_context()` here for test convenience."""
    return ExerciseRecommendationRuleContext(
        exercise=exercise or an_exercise_context(),
        goal=goal,
        safety_result=safety_result,
        readiness_result=readiness_result,
        progressive_overload=progressive_overload,
        declared_restrictions=declared_restrictions,
        available_equipment=available_equipment,
        recent_movement_patterns=recent_movement_patterns,
    )
