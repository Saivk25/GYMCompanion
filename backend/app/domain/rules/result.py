"""`RuleId` and `RuleResult`: what a single `Rule` evaluation produces, and
what `RuleEngine.evaluate()` produces after aggregating many of them.

`RuleId` lives here, not in `rule.py`, purely to avoid a circular import:
`RuleResult.triggered_rules` needs it as a field type, and `rule.py` needs
`RuleResult` as `Rule.evaluate()`'s return type — putting `RuleId` in
whichever module has no dependency on the other breaks the cycle. `Rule`
still re-exports it (`from app.domain.rules.result import RuleId`) so a
concrete rule author never needs to know this file split happened.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.rules.recommendation import Recommendation
from app.domain.rules.severity import RecommendationSeverity
from app.domain.shared_kernel.validation import ensure_not_empty
from app.domain.shared_kernel.value_object import ValueObject


@dataclass(frozen=True)
class RuleId(ValueObject):
    """A rule's stable identifier.

    Deliberately not a subclass of `app.domain.shared_kernel.EntityId`
    (a generated UUID) the way every aggregate's own id is. A `Rule` is
    code — one fixed instance per concrete rule, defined once, not created
    per request through a factory — and the Domain Model & Decision Engine
    Bible is explicit that "rule engines are versioned like code" (Section
    12) and that a past `Decision` snapshot must remain explainable by
    referencing exactly which rule fired, even after the rule set changes.
    A random UUID regenerated on every process restart could never serve
    as that stable reference; a human-chosen slug (e.g.
    `"safety.contraindication_check"`) can. See
    `docs/adr/0013-rule-engine-foundation.md`.

    Any non-empty string is accepted — this type enforces no naming
    convention (dotted namespace, case, etc.); that is left to whichever
    concrete rule engine defines its own `RuleId`s.
    """

    value: str

    def __post_init__(self) -> None:
        ensure_not_empty(self.value, "rule id")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, kw_only=True)
class RuleResult(ValueObject):
    """The outcome of evaluating one `Rule` against a `RuleContext` — and,
    identically shaped, the outcome of `RuleEngine.evaluate()` aggregating
    many of them (`engine.py`). One type serves both levels on purpose: a
    caller consuming an engine's output never needs to know whether it's
    looking at one rule's result or many rules' combined result, and a
    `RuleEngine`'s own output could itself be fed anywhere a single
    `RuleResult` is expected (e.g. nested composition by a future
    higher-level engine).

    Field meaning is the same at both levels:

    - `passed`: `True` only if nothing in this result's scope triggered.
    - `severity`: at the single-rule level, the evaluating `Rule`'s own
      classified severity (`Rule.severity`), always present regardless of
      pass/fail — it describes how severe *this class of check* is, not
      only how severe today's specific finding is. At the aggregate
      level, the highest severity among the results that triggered, or
      `RecommendationSeverity.INFO` if none did.
    - `explanation`: a human-readable account of what was found.
    - `recommendations`: advice attached by whichever rule(s) produced
      this result — may be non-empty even when `passed` is `True`.
    - `triggered_rules`: the ids of every rule that did not pass, within
      this result's scope. `()` when `passed` is `True`.
    """

    passed: bool
    severity: RecommendationSeverity
    explanation: str
    recommendations: tuple[Recommendation, ...] = field(default_factory=tuple)
    triggered_rules: tuple[RuleId, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        ensure_not_empty(self.explanation, "rule result explanation")
