"""`RecommendationSeverity`: the single severity scale shared by
`RuleResult` and `Recommendation`.

One scale for both, not two, because they describe the same underlying
concept from two angles: a `RuleResult.severity` is "how serious is what
this rule found," and a `Recommendation.severity` is "how seriously should
the user treat this piece of advice" — always derived from the rule that
raised it (see `rule.py`'s `Rule._fail()`/`Rule._pass()`).
"""

from enum import Enum

# Declaration order is deliberately least-to-most severe and is the single
# source of truth for ranking — nothing in this module relies on Python's
# default Enum member order for that, since `RecommendationSeverity` is a
# `str` subclass and `str.__lt__` would compare members lexicographically
# ("critical" < "warning") if anything ever called `<` on them directly.
# `engine.py`'s aggregation logic ranks explicitly via `_SEVERITY_RANK`
# instead of relying on either of those orderings implicitly.
_SEVERITY_ORDER = ("info", "advisory", "warning", "critical")


class RecommendationSeverity(str, Enum):
    """How seriously a triggered rule's finding should be treated.

    Four tiers, deliberately this increment's own general-purpose scale —
    the Domain Model & Decision Engine Bible's own language only names one
    tier explicitly ("Critical-class recommendations always require
    explicit user acceptance," Section 7.9's `Recommendation` state
    machine), not a full scale; the other three are this increment's own
    choice, not a Bible quote. See `docs/adr/0013-rule-engine-foundation.md`.
    """

    INFO = "info"
    ADVISORY = "advisory"
    WARNING = "warning"
    CRITICAL = "critical"


_SEVERITY_RANK: dict[RecommendationSeverity, int] = {
    RecommendationSeverity(value): rank for rank, value in enumerate(_SEVERITY_ORDER)
}


def severity_rank(severity: RecommendationSeverity) -> int:
    """Maps a severity to an integer rank (`INFO` lowest, `CRITICAL`
    highest) so callers can compare or sort severities explicitly and
    deterministically, without relying on `Enum` declaration order or the
    `str` mixin's lexicographic `__lt__`. Used by
    `engine.py`'s aggregation to find the most severe triggered result.
    """
    return _SEVERITY_RANK[severity]
