"""`SafetyRuleEngine`: the Safety-specific configuration of the shared
`RuleEngine[SafetyRuleContext]` (`app.domain.rules.engine`), evaluating
all five safety rules by default.

A subclass, not a wrapper, that overrides no behavior — the same
"configuration-only subclass" shape every prior concrete engine
establishes; see `docs/adr/0013-rule-engine-foundation.md`.

On this engine's authority relative to every other rule engine in this
codebase: the Domain Model & Decision Engine Bible names Safety Rules as
"the highest-authority engine in the system — can override any other
engine; is overridden by none" (Section 10.4), and its own decision-type
table marks "Safety / escalation go-no-go" as "Rules, exclusively" — no
statistical or AI layer even advises on it (Section 8, Table 41). This
package implements that authority only at the *evaluation* level: it
computes what a caller should know as accurately and conservatively as
its inputs allow. It does not — cannot, from inside `app/domain`, with no
knowledge of any other engine's own results — enforce that authority by
blocking a workout session, a plan, or another engine's output. Actually
combining this engine's `RuleResult` with, say, a future Workout Rules
engine's output and having Safety's CRITICAL findings actually override
the other's recommendation is an application-layer arbitration concern
(Bible Section 8.3, "Rule layer and AI layer disagree: Rule layer always
wins") that this phase does not build — see
`docs/adr/0018-safety-rule-engine-composition-and-authority.md`.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.domain.rules.engine import RuleEngine
from app.domain.rules.rule import Rule
from app.domain.safety.rules.context import SafetyRuleContext
from app.domain.safety.rules.contraindication_rule import ContraindicationRule
from app.domain.safety.rules.injury_rule import InjuryRule
from app.domain.safety.rules.readiness_safety_rule import ReadinessSafetyRule
from app.domain.safety.rules.soreness_rule import SorenessRule
from app.domain.safety.rules.workload_rule import WorkloadRule


def _default_rules() -> tuple[Rule[SafetyRuleContext], ...]:
    return (
        ReadinessSafetyRule(),
        SorenessRule(),
        WorkloadRule(),
        ContraindicationRule(),
        InjuryRule(),
    )


class SafetyRuleEngine(RuleEngine[SafetyRuleContext]):
    """Evaluates a `SafetyRuleContext` against `ReadinessSafetyRule`,
    `SorenessRule`, `WorkloadRule`, `ContraindicationRule`, and
    `InjuryRule` by default, and aggregates their results into one
    `RuleResult` — see `RuleEngine.evaluate()` for exactly how passed/
    severity/explanation/recommendations/triggered_rules are combined.

    Accepts an explicit `rules` override for testing or for a caller that
    wants a subset/reconfigured set of safety rules; the five defaults
    are used when omitted.
    """

    def __init__(self, rules: Sequence[Rule[SafetyRuleContext]] | None = None) -> None:
        super().__init__(rules if rules is not None else _default_rules())
