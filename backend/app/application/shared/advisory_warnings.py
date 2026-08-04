"""`advisory_warnings()`: formats a `RuleResult`'s `recommendations` as
human-readable strings, e.g. `"[advisory] consider adding more
fiber-rich foods"`.

Extracted here as a standalone refactor between Sprint 4 Phase 6
(Readiness) and Goal Application Use Cases, from 11 byte-identical
private copies (`_advisory_warnings()`) across Workout, Nutrition,
Progress, and Readiness handlers. Each copy was added independently, in
four different phases (`docs/adr/0024` through `docs/adr/0027`), each
justified at the time by "two call sites sharing one three-line
function is not yet the second real need" — correct reasoning each time
it was written, but nobody had tallied the running total across phases.
`docs/TECH_DEBT.md`'s TD-0001 tracked this duplication from the moment
an Application Layer consistency review first found it (post-Phase-5)
through the moment its own "9th call site" extraction trigger fired
(Phase 6, Readiness) to this extraction. See that entry for the full
history and the reasoning for not extracting sooner.

This function is a pure formatting utility over a Domain Layer type
(`RuleResult`, `app.domain.rules.result`) that every rule engine in this
codebase already produces — it contains no business logic of its own
(it does not decide what triggers a recommendation, only how to render
one that a `Rule` already produced), and no handler's orchestration
shape changes by calling it here instead of a local copy: every calling
handler still evaluates its own rule engine, still surfaces the result
as `ApplicationResult.warnings`, and still treats the engine as
evaluation-only, exactly as before extraction. This is why it belongs
in `app.application.shared` rather than `app.domain.rules`: it has
nothing to do with rule evaluation itself, only with how one Application
Layer handler formats another layer's already-computed output for a
caller.
"""

from __future__ import annotations

from app.domain.rules.result import RuleResult


def advisory_warnings(result: RuleResult) -> tuple[str, ...]:
    """Formats every `Recommendation` in `result.recommendations` as
    `f"[{severity}] {message}"`, in the order `RuleEngine.evaluate()`
    produced them. Returns `()` when `result.recommendations` is empty —
    a `RuleResult` that passed with nothing to recommend is not an
    error, and neither is an empty return here.
    """
    return tuple(
        f"[{recommendation.severity.value}] {recommendation.message}"
        for recommendation in result.recommendations
    )
