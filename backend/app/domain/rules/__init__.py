"""The Rule Engine foundation: Sprint 3's shared infrastructure for every
future deterministic decision engine, built on the Sprint 1 shared kernel
(`app.domain.shared_kernel`). Domain Model & Decision Engine Bible,
Section 8.1's "Deterministic Rule Layer" ("applies hard gates and
guardrails first ... can block or constrain everything downstream;
nothing downstream can override it") and Section 10's nine named rule
engines (Workout, Nutrition, Recovery, Safety, Recommendation,
Notification, Progress, Analytics, AI Validation) are what this package
exists to eventually support.

This increment implements no fitness logic whatsoever — no readiness
scoring, nutrition advice, workout recommendations, goal evaluation,
progressive overload, recovery, safety, or exercise substitution rules.
It implements only the reusable architecture: `Rule`, `RuleContext`,
`RuleResult`, `RuleEngine`, `Recommendation`, and
`RecommendationSeverity`. See
`docs/adr/0013-rule-engine-foundation.md` for the full architecture
rationale, including why there is no `repository.py` in this package
(rules are code-defined instances, not persisted aggregates — nothing
here needs a `Repository[TAggregate, TId]`).

Depends on nothing outside the Python standard library and
`app.domain.shared_kernel` — enforced by the same statically-checked rule
as the rest of `app/domain` (`tests/domain/test_import_boundaries.py`).
"""

from app.domain.rules.context import RuleContext
from app.domain.rules.engine import RuleEngine
from app.domain.rules.recommendation import Recommendation
from app.domain.rules.result import RuleId, RuleResult
from app.domain.rules.rule import Rule
from app.domain.rules.severity import RecommendationSeverity, severity_rank

__all__ = [
    "Recommendation",
    "RecommendationSeverity",
    "Rule",
    "RuleContext",
    "RuleEngine",
    "RuleId",
    "RuleResult",
    "severity_rank",
]
