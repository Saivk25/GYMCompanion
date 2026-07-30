"""`SorenessRule`: detects excessive soreness requiring caution, from the
same `ReadinessContext.soreness_level` field
`app.domain.readiness.rules.soreness_rule.SorenessRule` already
evaluates — deliberately re-evaluated here, not imported or reused.

The two rules answer different questions at different severities:
Readiness's own `SorenessRule` is general training advice ("soreness is
elevated, consider a lighter session", WARNING). This rule asks whether
soreness is severe enough that training itself is a safety concern
("this level of soreness requires caution", CRITICAL by default, and a
stricter threshold). Two rule engines legitimately holding independent
opinions about the same underlying field is expected, not a bug — each
serves its own engine's purpose, the same "independent rules, no shared
state" posture every rule engine in this codebase follows, now extended
across engine boundaries rather than only within one engine's own rule
set. See `docs/adr/0018-safety-rule-engine-composition-and-authority.md`.
"""

from __future__ import annotations

from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule
from app.domain.rules.severity import RecommendationSeverity
from app.domain.safety.rules.context import SafetyRuleContext

_DEFAULT_CRITICAL_SORENESS = 9


class SorenessRule(Rule[SafetyRuleContext]):
    """Triggers when `context.readiness.soreness_level` is at or above
    `critical_soreness` (9 out of 10 by default — stricter than
    Readiness's own advisory `SorenessRule`, which defaults to 7).
    Passes when `context.readiness` is `None`, or when
    `soreness_level` is `None` or below the critical threshold."""

    def __init__(
        self,
        *,
        critical_soreness: int = _DEFAULT_CRITICAL_SORENESS,
        severity: RecommendationSeverity = RecommendationSeverity.CRITICAL,
        rule_id: RuleId | None = None,
    ) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("safety.soreness"),
            name="Soreness Safety",
            description="Detects excessive soreness that requires caution before training.",
            severity=severity,
        )
        self._critical_soreness = critical_soreness

    def evaluate(self, context: SafetyRuleContext) -> RuleResult:
        readiness = context.readiness
        if readiness is None:
            return self._pass("No readiness check-in supplied; cannot evaluate soreness safety.")

        soreness_level = readiness.soreness_level
        if soreness_level is None:
            return self._pass("No soreness level recorded; cannot evaluate soreness safety.")

        if soreness_level.value >= self._critical_soreness:
            return self._fail(
                f"Soreness level of {soreness_level.value} is at or above the critical "
                f"threshold of {self._critical_soreness}.",
                recommendations=(
                    Recommendation(
                        severity=self.severity,
                        message="Soreness is severe enough to require caution — consider "
                        "resting the affected area before training it again.",
                    ),
                ),
            )

        return self._pass(
            f"Soreness level of {soreness_level.value} is below the critical threshold of "
            f"{self._critical_soreness}."
        )
