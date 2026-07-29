"""The Readiness Rule Engine: Sprint 3 Phase 2's first concrete
deterministic rule engine, built on the Phase 1 Rule Engine foundation
(`app.domain.rules`) and the Readiness aggregate (`app.domain.readiness`).
Domain Model & Decision Engine Bible, Section 4.8 (`ReadinessCheckIn`) is
the data source; Section 10.3's "Recovery Rules" ("governs the
RecoveryState computation and deload triggering") is the closest named
engine, though this phase deliberately implements a smaller slice of it —
see the module docstring below and
`docs/adr/0014-readiness-rule-composition.md`.

This engine evaluates a user's readiness inputs and produces deterministic
`Recommendation`s only — no AI, no recovery score, no fatigue score, no
training load, no workout recommendations, no scheduling. Those all
require either a window of check-ins (`RecoveryState`, not built) or
cross-domain data (`Workout`, `WorkoutSession`) this phase deliberately
does not read.

Five independent rules (`SleepRule`, `EnergyRule`, `StressRule`,
`SorenessRule`, `RecoveryRule`), each evaluating one or two fields of
`ReadinessRuleContext` against a fixed, documented threshold, composed by
`ReadinessRuleEngine` (itself a thin, behavior-preserving configuration of
the shared `RuleEngine[ReadinessRuleContext]`). See
`docs/adr/0014-readiness-rule-composition.md` for why independent rules
were chosen over one monolithic evaluator.

Depends on nothing outside the Python standard library,
`app.domain.shared_kernel`, `app.domain.rules` (the Phase 1 foundation),
and `app.domain.readiness` (its own parent aggregate) — enforced by the
same statically-checked rule as the rest of `app/domain`
(`tests/domain/test_import_boundaries.py`).
"""

from app.domain.readiness.rules.context import ReadinessRuleContext
from app.domain.readiness.rules.energy_rule import EnergyRule
from app.domain.readiness.rules.readiness_rule_engine import ReadinessRuleEngine
from app.domain.readiness.rules.recovery_rule import RecoveryRule
from app.domain.readiness.rules.sleep_rule import SleepRule
from app.domain.readiness.rules.soreness_rule import SorenessRule
from app.domain.readiness.rules.stress_rule import StressRule

__all__ = [
    "EnergyRule",
    "ReadinessRuleContext",
    "ReadinessRuleEngine",
    "RecoveryRule",
    "SleepRule",
    "SorenessRule",
    "StressRule",
]
