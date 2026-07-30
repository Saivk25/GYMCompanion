"""`ExerciseRecommendationRuleEngine`: composes the five exercise
recommendation rules into one `RuleEngine[ExerciseRecommendationRuleContext]`,
the "configuration-only subclass" pattern every concrete rule engine in
this codebase follows (`docs/adr/0013-rule-engine-foundation.md`).

Aggregated `passed=False` means "exclude this candidate" — only
`ContraindicatedExerciseRule` and `EquipmentRule` ever fail, matching
Table 48's "removed from candidates" gates. `ExerciseSelectionRule`,
`MovementBalanceRule`, and `ProgressionStageRule` never fail; their
advice surfaces only through `recommendations`, matching Table 48's
"biases... ranking" language — a passing aggregate result can still
carry recommendations worth showing.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.domain.exercise.rules.context import ExerciseRecommendationRuleContext
from app.domain.exercise.rules.contraindicated_exercise_rule import ContraindicatedExerciseRule
from app.domain.exercise.rules.equipment_rule import EquipmentRule
from app.domain.exercise.rules.exercise_selection_rule import ExerciseSelectionRule
from app.domain.exercise.rules.movement_balance_rule import MovementBalanceRule
from app.domain.exercise.rules.progression_stage_rule import ProgressionStageRule
from app.domain.rules.engine import RuleEngine
from app.domain.rules.rule import Rule


def _default_rules() -> tuple[Rule[ExerciseRecommendationRuleContext], ...]:
    return (
        ExerciseSelectionRule(),
        ContraindicatedExerciseRule(),
        MovementBalanceRule(),
        EquipmentRule(),
        ProgressionStageRule(),
    )


class ExerciseRecommendationRuleEngine(RuleEngine[ExerciseRecommendationRuleContext]):
    """Evaluation-only, the same authority every prior engine in this
    codebase documents for itself: it computes findings about one
    candidate exercise, it does not itself generate a workout, schedule
    anything, or prescribe sets/reps.
    """

    def __init__(
        self, rules: Sequence[Rule[ExerciseRecommendationRuleContext]] | None = None
    ) -> None:
        super().__init__(rules if rules is not None else _default_rules())
