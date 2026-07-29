"""`Rule`: the abstract base every concrete deterministic rule — in every
future rule engine this package exists to support — subclasses.

Generic over the `RuleContext` subtype it evaluates against
(`Rule[ReadinessRuleContext]`, say), so a rule written for one engine's
context can never be accidentally registered with another engine's
`RuleEngine` — mypy rejects the mismatch at the type level, before any
test would have to catch it at runtime.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Generic, TypeVar

from app.domain.rules.context import RuleContext
from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.severity import RecommendationSeverity
from app.domain.shared_kernel.validation import ensure_not_empty

TContext = TypeVar("TContext", bound=RuleContext)

__all__ = ["Rule", "RuleId", "TContext"]


class Rule(ABC, Generic[TContext]):
    """A single named, deterministic check against a `RuleContext`.

    Concrete rules subclass this and implement only `evaluate()` — `id`,
    `name`, `description`, and `severity` are stored and exposed by this
    base class's own constructor, not boilerplate every rule author has to
    repeat. `evaluate()` is expected to be a pure function of `context`:
    no I/O, no wall-clock reads, no reliance on any state beyond what
    `context` and this rule's own (immutable, constructor-set) fields
    provide — see `RuleEngine`'s own docstring (`engine.py`) for why that
    matters at the aggregate-evaluation level too.
    """

    def __init__(
        self,
        *,
        rule_id: RuleId,
        name: str,
        description: str,
        severity: RecommendationSeverity,
    ) -> None:
        self._id = rule_id
        self._name = ensure_not_empty(name, "rule name")
        self._description = ensure_not_empty(description, "rule description")
        self._severity = severity

    @property
    def id(self) -> RuleId:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def severity(self) -> RecommendationSeverity:
        """This rule's own classified severity — how serious a triggered
        finding from this specific rule is. Fixed per rule instance, not
        computed per evaluation; a rule that checks something inherently
        safety-critical is `CRITICAL` every time it triggers, not
        sometimes `WARNING` depending on the input.
        """
        return self._severity

    @abstractmethod
    def evaluate(self, context: TContext) -> RuleResult:
        """Evaluates this rule against `context` and returns exactly one
        `RuleResult`. Must be side-effect free and deterministic: calling
        this twice with an equal `context` must return an equal result.
        Build the return value with `_pass()`/`_fail()` below rather than
        constructing `RuleResult` directly — they fill in `rule_id` and
        `severity` from this rule's own identity consistently.
        """
        raise NotImplementedError  # pragma: no cover — abstract, always overridden

    def _pass(
        self, explanation: str, *, recommendations: Sequence[Recommendation] = ()
    ) -> RuleResult:
        """Builds the `RuleResult` for a successful evaluation: `passed`
        is `True`, `triggered_rules` is empty. `recommendations` may still
        be non-empty — passing does not preclude offering advice (e.g.
        positive reinforcement), it only means nothing was flagged.
        """
        return RuleResult(
            passed=True,
            severity=self._severity,
            explanation=explanation,
            recommendations=tuple(recommendations),
            triggered_rules=(),
        )

    def _fail(
        self, explanation: str, *, recommendations: Sequence[Recommendation] = ()
    ) -> RuleResult:
        """Builds the `RuleResult` for a failed (triggered) evaluation:
        `passed` is `False` and `triggered_rules` is `(self.id,)`.
        """
        return RuleResult(
            passed=False,
            severity=self._severity,
            explanation=explanation,
            recommendations=tuple(recommendations),
            triggered_rules=(self._id,),
        )
