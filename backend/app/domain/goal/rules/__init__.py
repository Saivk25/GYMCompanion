"""The Goal Alignment Rule Engine: Sprint 3 Phase 4's third concrete
deterministic rule engine, built on the Phase 1 Rule Engine foundation
(`app.domain.rules`), the Goal aggregate (`app.domain.goal`), and the
Progress aggregate (`app.domain.progress`), following the independent-
rule composition strategy `app.domain.readiness.rules` (Phase 2) and
`app.domain.nutrition.rules` (Phase 3) already established.

This engine evaluates whether a user's current state — captured as an
immutable `GoalContext` snapshot and an optional `ProgressContext`
snapshot — aligns with one of their active goals, and produces
deterministic `Recommendation`s only. No AI, no workout planning, no
progressive overload, no exercise recommendations, no training load, no
nutrition advice.

Five independent rules (`TargetDateRule`, `BodyWeightRule`,
`BodyFatRule`, `StrengthGoalRule`, `PriorityRule`), each evaluating one
dimension of goal alignment against `GoalAlignmentRuleContext`, composed
by `GoalAlignmentRuleEngine` (itself a thin, behavior-preserving
configuration of the shared `RuleEngine[GoalAlignmentRuleContext]`). See
`docs/adr/0016-goal-alignment-combines-whole-snapshots.md` for why this
context references whole `GoalContext`/`ProgressContext` snapshots rather
than flattening their fields (unlike Readiness's and Nutrition's own
contexts), why `reference_date` is an explicit field rather than a
wall-clock read, and why every rule here shares the same "only Active
goals" guard.

Depends on nothing outside the Python standard library,
`app.domain.shared_kernel`, `app.domain.rules` (the Phase 1 foundation),
`app.domain.goal` (its own parent aggregate), and `app.domain.progress`
(the second aggregate this engine reads) — enforced by the same
statically-checked rule as the rest of `app/domain`
(`tests/domain/test_import_boundaries.py`).
"""

from app.domain.goal.rules.body_fat_rule import BodyFatRule
from app.domain.goal.rules.body_weight_rule import BodyWeightRule
from app.domain.goal.rules.context import GoalAlignmentRuleContext
from app.domain.goal.rules.goal_alignment_rule_engine import GoalAlignmentRuleEngine
from app.domain.goal.rules.priority_rule import PriorityRule
from app.domain.goal.rules.strength_goal_rule import StrengthGoalRule
from app.domain.goal.rules.target_date_rule import TargetDateRule

__all__ = [
    "BodyFatRule",
    "BodyWeightRule",
    "GoalAlignmentRuleContext",
    "GoalAlignmentRuleEngine",
    "PriorityRule",
    "StrengthGoalRule",
    "TargetDateRule",
]
