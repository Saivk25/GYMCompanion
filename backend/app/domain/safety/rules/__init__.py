"""The Safety Rule Engine: Sprint 3 Phase 6's fifth concrete deterministic
rule engine, built on the Phase 1 Rule Engine foundation
(`app.domain.rules`) and, unlike every prior concrete engine, composed
from *other engines'* context types (`app.domain.readiness.context.
ReadinessContext`, `app.domain.workout.rules.context.
ProgressiveOverloadRuleContext`) rather than one aggregate of its own —
see the parent `app.domain.safety` package's docstring for why no Safety
aggregate exists yet.

This engine evaluates whether it is currently safe for a user to train,
from immutable snapshots only, and produces deterministic
`Recommendation`s alone — no AI, no exercise substitution, no workout
planning or generation.

Five independent rules (`ReadinessSafetyRule`, `SorenessRule`,
`WorkloadRule`, `ContraindicationRule`, `InjuryRule`), composed by
`SafetyRuleEngine` (itself a thin, behavior-preserving configuration of
the shared `RuleEngine[SafetyRuleContext]`). Missing data passes with an
explanation rather than failing, the same convention every prior engine
in this codebase follows — see each rule's own docstring for what
"missing" means for it specifically. See
`docs/adr/0018-safety-rule-engine-composition-and-authority.md` for the
architectural decisions specific to composing a context from other
engines' types, two rules deliberately re-evaluating fields another
engine already reads for a different purpose, and this engine's
authority relative to the rest of the codebase.

Depends on nothing outside the Python standard library,
`app.domain.shared_kernel`, `app.domain.rules` (the Phase 1 foundation),
`app.domain.readiness` (for `ReadinessContext`), and
`app.domain.workout.rules` (for `ProgressiveOverloadRuleContext`) —
enforced by the same statically-checked rule as the rest of `app/domain`
(`tests/domain/test_import_boundaries.py`).

No `repository.py` in this package, the same reasoning
`app.domain.rules.__init__`'s own docstring documents: this engine
consumes context objects, never loads its own data.
"""

from app.domain.safety.rules.context import ActiveInjury, DeclaredRestriction, SafetyRuleContext
from app.domain.safety.rules.contraindication_rule import ContraindicationRule
from app.domain.safety.rules.injury_rule import InjuryRule
from app.domain.safety.rules.readiness_safety_rule import ReadinessSafetyRule
from app.domain.safety.rules.safety_rule_engine import SafetyRuleEngine
from app.domain.safety.rules.soreness_rule import SorenessRule
from app.domain.safety.rules.workload_rule import WorkloadRule

__all__ = [
    "ActiveInjury",
    "ContraindicationRule",
    "DeclaredRestriction",
    "InjuryRule",
    "ReadinessSafetyRule",
    "SafetyRuleContext",
    "SafetyRuleEngine",
    "SorenessRule",
    "WorkloadRule",
]
