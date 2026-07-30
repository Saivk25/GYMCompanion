"""`GoalAlignmentRuleEngine`: the Goal-Alignment-specific configuration of
the shared `RuleEngine[GoalAlignmentRuleContext]`
(`app.domain.rules.engine`), evaluating all five goal alignment rules by
default.

A subclass, not a wrapper — but it overrides no behavior, the same
construction-only pattern
`app.domain.readiness.rules.readiness_rule_engine.ReadinessRuleEngine`
and `app.domain.nutrition.rules.nutrition_rule_engine.NutritionRuleEngine`
already established. This class only wires up the five default rules and
gives that configuration a discoverable name and a zero-argument
constructor.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.domain.goal.rules.body_fat_rule import BodyFatRule
from app.domain.goal.rules.body_weight_rule import BodyWeightRule
from app.domain.goal.rules.context import GoalAlignmentRuleContext
from app.domain.goal.rules.priority_rule import PriorityRule
from app.domain.goal.rules.strength_goal_rule import StrengthGoalRule
from app.domain.goal.rules.target_date_rule import TargetDateRule
from app.domain.rules.engine import RuleEngine
from app.domain.rules.rule import Rule


def _default_rules() -> tuple[Rule[GoalAlignmentRuleContext], ...]:
    return (
        TargetDateRule(),
        BodyWeightRule(),
        BodyFatRule(),
        StrengthGoalRule(),
        PriorityRule(),
    )


class GoalAlignmentRuleEngine(RuleEngine[GoalAlignmentRuleContext]):
    """Evaluates a `GoalAlignmentRuleContext` against `TargetDateRule`,
    `BodyWeightRule`, `BodyFatRule`, `StrengthGoalRule`, and
    `PriorityRule` by default, and aggregates their results into one
    `RuleResult` — see `RuleEngine.evaluate()` for exactly how
    passed/severity/explanation/recommendations/triggered_rules are
    combined.

    Accepts an explicit `rules` override for testing or for a caller that
    wants a subset/reconfigured set of goal alignment rules; the five
    defaults are used when omitted.
    """

    def __init__(self, rules: Sequence[Rule[GoalAlignmentRuleContext]] | None = None) -> None:
        super().__init__(rules if rules is not None else _default_rules())
