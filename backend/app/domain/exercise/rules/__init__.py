"""The Exercise Recommendation Rule Engine: Sprint 3 Phase 9's eighth
concrete deterministic rule engine, built on the Phase 1 Rule Engine
foundation (`app.domain.rules`), the Exercise aggregate
(`app.domain.exercise`), and — unlike any prior engine — by *composing
the already-computed outputs* of the Safety, Progressive Overload, and
Readiness engines, rather than either aggregate data or another
engine's raw context.

This engine evaluates whether one candidate `Exercise` should be
recommended right now, one candidate per evaluation (see
`context.py`'s own docstring), and produces deterministic
`Recommendation`s only — no AI, no workout generation, no scheduling,
no sets/reps prescriptions.

Five independent rules (`ExerciseSelectionRule`,
`ContraindicatedExerciseRule`, `MovementBalanceRule`, `EquipmentRule`,
`ProgressionStageRule`), composed by `ExerciseRecommendationRuleEngine`
(itself a thin, behavior-preserving configuration of the shared
`RuleEngine[ExerciseRecommendationRuleContext]`). Only
`ContraindicatedExerciseRule` and `EquipmentRule` can fail (Domain
Model & Decision Engine Bible Table 48's "removed from candidates"
gates); the other three are pure advisory biases (Table 48's
"biases... ranking" language) that always pass while still attaching
`Recommendation`s. See
`docs/adr/0021-exercise-recommendation-composes-rule-outputs.md` for
the full reasoning behind composing other engines' `RuleResult`s
without duplicating their decision logic, and for the small new
supplied value objects (`declared_restrictions`, `available_equipment`,
`recent_movement_patterns`) this package needs that no existing
aggregate or context yet carries.

Depends on nothing outside the Python standard library,
`app.domain.shared_kernel`, `app.domain.rules` (the Phase 1
foundation), `app.domain.exercise` (its own parent aggregate),
`app.domain.goal` (for `GoalContext`), `app.domain.safety.rules` (for
`DeclaredRestriction`), and `app.domain.workout.rules` (for
`ProgressiveOverloadRuleContext`) — enforced by the same
statically-checked rule as the rest of `app/domain`
(`tests/domain/test_import_boundaries.py`).

No `repository.py` in this package, the same reasoning
`app.domain.rules.__init__`'s own docstring documents: this engine
consumes context objects, never loads its own data.
"""

from app.domain.exercise.rules.context import ExerciseRecommendationRuleContext
from app.domain.exercise.rules.contraindicated_exercise_rule import ContraindicatedExerciseRule
from app.domain.exercise.rules.equipment_rule import EquipmentRule
from app.domain.exercise.rules.exercise_recommendation_rule_engine import (
    ExerciseRecommendationRuleEngine,
)
from app.domain.exercise.rules.exercise_selection_rule import ExerciseSelectionRule
from app.domain.exercise.rules.movement_balance_rule import MovementBalanceRule
from app.domain.exercise.rules.progression_stage_rule import ProgressionStageRule

__all__ = [
    "ContraindicatedExerciseRule",
    "EquipmentRule",
    "ExerciseRecommendationRuleContext",
    "ExerciseRecommendationRuleEngine",
    "ExerciseSelectionRule",
    "MovementBalanceRule",
    "ProgressionStageRule",
]
