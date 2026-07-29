"""Shared test helpers for the Rule Engine foundation's test suite.

Not itself a test file (no `test_` prefix, so pytest never collects it) —
mirrors every other aggregate's `tests/domain/*/factories.py` reasoning.

`Rule` and `RuleContext` are both abstract/empty by design (see their own
module docstrings) — this package's tests need at least one concrete
`RuleContext` and a small family of concrete `Rule`s to exercise the
shared infrastructure against, standing in for what a real future engine
(e.g. Safety Rules) would define for itself.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.rules.context import RuleContext
from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule
from app.domain.rules.severity import RecommendationSeverity


@dataclass(frozen=True, kw_only=True)
class DummyContext(RuleContext):
    """A minimal concrete `RuleContext` — one field, just enough for a
    rule to branch on in tests."""

    value: int = 0


class AlwaysPassRule(Rule[DummyContext]):
    """A rule that always passes, optionally attaching recommendations
    even though it passed (allowed — see `Rule._pass()`'s docstring)."""

    def __init__(
        self,
        *,
        rule_id: RuleId | None = None,
        severity: RecommendationSeverity = RecommendationSeverity.INFO,
        recommendations: tuple[Recommendation, ...] = (),
    ) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("test.always_pass"),
            name="Always Pass",
            description="A rule that always passes, for testing.",
            severity=severity,
        )
        self._recommendations = recommendations

    def evaluate(self, context: DummyContext) -> RuleResult:
        return self._pass("always passes", recommendations=self._recommendations)


class AlwaysFailRule(Rule[DummyContext]):
    """A rule that always fails (triggers)."""

    def __init__(
        self,
        *,
        rule_id: RuleId | None = None,
        severity: RecommendationSeverity = RecommendationSeverity.WARNING,
        explanation: str = "always fails",
        recommendations: tuple[Recommendation, ...] = (),
    ) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("test.always_fail"),
            name="Always Fail",
            description="A rule that always fails, for testing.",
            severity=severity,
        )
        self._explanation = explanation
        self._recommendations = recommendations

    def evaluate(self, context: DummyContext) -> RuleResult:
        return self._fail(self._explanation, recommendations=self._recommendations)


class ThresholdRule(Rule[DummyContext]):
    """Fails when `context.value` is below a configured threshold —
    the one rule in this factory module that actually branches on its
    context, standing in for a real conditional rule."""

    def __init__(self, *, threshold: int, rule_id: RuleId | None = None) -> None:
        super().__init__(
            rule_id=rule_id or RuleId("test.threshold"),
            name="Threshold",
            description="Fails when context.value is below threshold.",
            severity=RecommendationSeverity.CRITICAL,
        )
        self._threshold = threshold

    def evaluate(self, context: DummyContext) -> RuleResult:
        if context.value >= self._threshold:
            return self._pass(f"{context.value} meets the threshold of {self._threshold}")
        return self._fail(f"{context.value} is below the threshold of {self._threshold}")
