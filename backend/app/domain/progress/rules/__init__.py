"""The Progress Evaluation Rule Engine: Sprint 3 Phase 7's sixth concrete
deterministic rule engine, built on the Phase 1 Rule Engine foundation
(`app.domain.rules`), the Progress aggregate (`app.domain.progress`),
and the Goal aggregate's own context type
(`app.domain.goal.context.GoalContext`).

This engine evaluates whether a user's historical body-composition and
measurement trends are progressing toward active goals, from immutable
snapshots only, and produces deterministic `Recommendation`s alone — no
AI, no workout planning, no exercise recommendation, no training load.

Five independent rules (`BodyWeightRule`, `BodyFatRule`,
`MeasurementTrendRule`, `ConsistencyRule`, `PlateauRule`), composed by
`ProgressEvaluationRuleEngine` (itself a thin, behavior-preserving
configuration of the shared
`RuleEngine[ProgressEvaluationRuleContext]`). Continues the "missing data
passes" convention every prior engine follows, with one deliberate,
Bible-grounded exception: `ConsistencyRule` fails on insufficient or
stale data rather than passing, implementing the Domain Model & Decision
Engine Bible's own "Minimum evidence rule" (Table 54). See
`docs/adr/0019-progress-evaluation-consistency-and-plateau-scope.md` for
the full reasoning, including why `PlateauRule` is deliberately
goal-agnostic while `BodyWeightRule`/`BodyFatRule` are not.

This package is this codebase's first slice of what
`app.domain.progress.progress`'s own module docstring already
anticipates — "Progress Intelligence... a separate, not-yet-built
context" — scoped to the Bible's Section 10.7 "Progress Rules"
(deterministic trend/plateau gating) only, not the Statistical layer's
actual slope/regression computation behind a real `Trend`/`Forecast`
entity, which remains unbuilt.

Depends on nothing outside the Python standard library,
`app.domain.shared_kernel`, `app.domain.rules` (the Phase 1 foundation),
`app.domain.progress` (its own parent aggregate), and `app.domain.goal`
(for `GoalContext`) — enforced by the same statically-checked rule as
the rest of `app/domain` (`tests/domain/test_import_boundaries.py`).

No `repository.py` in this package, the same reasoning
`app.domain.rules.__init__`'s own docstring documents: this engine
consumes context objects, never loads its own data.
"""

from app.domain.progress.rules.body_fat_rule import BodyFatRule
from app.domain.progress.rules.body_weight_rule import BodyWeightRule
from app.domain.progress.rules.consistency_rule import ConsistencyRule
from app.domain.progress.rules.context import ProgressEvaluationRuleContext
from app.domain.progress.rules.measurement_trend_rule import MeasurementTrendRule
from app.domain.progress.rules.plateau_rule import PlateauRule
from app.domain.progress.rules.progress_evaluation_rule_engine import ProgressEvaluationRuleEngine

__all__ = [
    "BodyFatRule",
    "BodyWeightRule",
    "ConsistencyRule",
    "MeasurementTrendRule",
    "PlateauRule",
    "ProgressEvaluationRuleContext",
    "ProgressEvaluationRuleEngine",
]
