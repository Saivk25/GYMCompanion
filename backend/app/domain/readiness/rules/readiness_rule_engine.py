"""`ReadinessRuleEngine`: the Readiness-specific configuration of the
shared `RuleEngine[ReadinessRuleContext]` (`app.domain.rules.engine`),
evaluating all five readiness rules by default.

A subclass, not a wrapper — but it overrides no behavior.
`docs/adr/0013-rule-engine-foundation.md` (Sprint 3, Phase 1) says every
concrete engine is expected to be "an instance of `RuleEngine[TheirContext]`
... not a subclass overriding `RuleEngine`'s behavior." That guidance is
about behavior, not construction: this class adds no method, changes no
aggregation logic, and does not touch `evaluate()`. Its only job is
giving the five-rule, `ReadinessRuleContext`-typed configuration a
discoverable name and a zero-argument constructor, which a bare
`RuleEngine([SleepRule(), EnergyRule(), ...])` call at every use site
would not provide. `isinstance(engine, RuleEngine)` is `True`, and every
`RuleEngine` guarantee (deterministic, side-effect free — see that
class's own docstring) holds unchanged.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.domain.readiness.rules.context import ReadinessRuleContext
from app.domain.readiness.rules.energy_rule import EnergyRule
from app.domain.readiness.rules.recovery_rule import RecoveryRule
from app.domain.readiness.rules.sleep_rule import SleepRule
from app.domain.readiness.rules.soreness_rule import SorenessRule
from app.domain.readiness.rules.stress_rule import StressRule
from app.domain.rules.engine import RuleEngine
from app.domain.rules.rule import Rule


def _default_rules() -> tuple[Rule[ReadinessRuleContext], ...]:
    return (
        SleepRule(),
        EnergyRule(),
        StressRule(),
        SorenessRule(),
        RecoveryRule(),
    )


class ReadinessRuleEngine(RuleEngine[ReadinessRuleContext]):
    """Evaluates a `ReadinessRuleContext` against `SleepRule`,
    `EnergyRule`, `StressRule`, `SorenessRule`, and `RecoveryRule` by
    default, and aggregates their results into one `RuleResult` — see
    `RuleEngine.evaluate()` for exactly how passed/severity/explanation/
    recommendations/triggered_rules are combined.

    Accepts an explicit `rules` override for testing or for a caller that
    wants a subset/reconfigured set of readiness rules; the five defaults
    are used when omitted.
    """

    def __init__(self, rules: Sequence[Rule[ReadinessRuleContext]] | None = None) -> None:
        super().__init__(rules if rules is not None else _default_rules())
