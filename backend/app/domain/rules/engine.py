"""`RuleEngine`: evaluates a fixed set of `Rule`s against one `RuleContext`
and aggregates their individual `RuleResult`s into one combined
`RuleResult`.

This is the piece the task's Goal calls out by name: "the common
architecture for rule evaluation" every future concrete engine (Workout
Rules, Safety Rules, and the rest of the Bible's nine, Section 10) is
meant to be built as an instance of, not a reimplementation of.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Generic

from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule, TContext
from app.domain.rules.severity import RecommendationSeverity, severity_rank

_NO_RULES_TRIGGERED_EXPLANATION = "No rules triggered."


class RuleEngine(Generic[TContext]):
    """Holds an ordered, immutable set of `Rule[TContext]` and evaluates
    all of them against one `TContext`, deterministically and without side
    effects: the same `rules` and an equal `context` always produce an
    equal `RuleResult`, and evaluating never mutates `context`, any rule,
    or any state outside this call. `RuleEngine` itself carries no other
    behavior — no persistence, no scheduling, no I/O — those are concerns
    for whatever future application-layer code owns calling it.

    Deliberately holds no context-specific knowledge of its own: it does
    not know what a "readiness" or "safety" rule is, only that it has been
    handed some `Rule[TContext]`s and one `TContext` to run them against.
    Every future concrete engine (Bible Section 10's nine) is expected to
    be *an instance of this class*, configured with that engine's own
    rules and context type, not a subclass overriding its behavior.
    """

    def __init__(self, rules: Sequence[Rule[TContext]]) -> None:
        self._rules: tuple[Rule[TContext], ...] = tuple(rules)

    @property
    def rules(self) -> tuple[Rule[TContext], ...]:
        return self._rules

    def evaluate(self, context: TContext) -> RuleResult:
        """Evaluates every rule against `context`, in registration order,
        and aggregates the individual results into one `RuleResult`:

        - `passed`: `True` only if every rule passed.
        - `severity`: the highest severity among the rules that
          triggered (`severity_rank`, not `Enum` declaration order or
          `str` comparison — see `severity.py`), or `INFO` if none did.
        - `explanation`: the triggered rules' own explanations, joined in
          evaluation order, or a fixed "No rules triggered." when none
          did.
        - `recommendations`: every recommendation from every individual
          result (triggered or not), flattened in evaluation order.
        - `triggered_rules`: the ids of every rule that did not pass, in
          evaluation order.

        Evaluating an empty rule set is well-defined, not an error: it
        returns a passing result with no findings — the same shape a real
        rule set produces when nothing happens to trigger.
        """
        results = tuple(rule.evaluate(context) for rule in self._rules)
        return _aggregate(results)


def _aggregate(results: tuple[RuleResult, ...]) -> RuleResult:
    triggered_results = tuple(result for result in results if not result.passed)

    triggered_rules: tuple[RuleId, ...] = tuple(
        rule_id for result in triggered_results for rule_id in result.triggered_rules
    )
    recommendations: tuple[Recommendation, ...] = tuple(
        recommendation for result in results for recommendation in result.recommendations
    )
    severity = _highest_severity(result.severity for result in triggered_results)
    explanation = (
        "; ".join(result.explanation for result in triggered_results)
        if triggered_results
        else _NO_RULES_TRIGGERED_EXPLANATION
    )

    return RuleResult(
        passed=not triggered_results,
        severity=severity,
        explanation=explanation,
        recommendations=recommendations,
        triggered_rules=triggered_rules,
    )


def _highest_severity(severities: Iterable[RecommendationSeverity]) -> RecommendationSeverity:
    ranked = sorted(severities, key=severity_rank, reverse=True)
    return ranked[0] if ranked else RecommendationSeverity.INFO
