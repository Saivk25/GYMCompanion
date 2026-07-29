"""`RuleContext`: the extensibility point every future concrete rule
engine plugs its own input shape into.

Deliberately an empty marker base class, not a struct with fields of its
own. Each of the nine rule engines named in the Domain Model & Decision
Engine Bible (Section 10: Workout, Nutrition, Recovery, Safety,
Recommendation, Notification, Progress, Analytics, AI Validation) will
need a completely different input snapshot — a Safety context needs
active `SafetyFlag`s and contraindication tags; a Recovery context needs a
window of `ReadinessCheckIn`s. Giving `RuleContext` fields today (even one
as apparently-universal as a timestamp) would mean guessing at a shape
every one of those nine engines is forced to inherit, for a need
(staleness/recency gating for the Decision Engine's confidence scoring,
Bible Section 8.4) that belongs to a future increment this one explicitly
excludes. See `docs/adr/0013-rule-engine-foundation.md`.

A concrete future context subclasses this directly, typically as its own
frozen dataclass:

    @dataclass(frozen=True, kw_only=True)
    class ReadinessRuleContext(RuleContext):
        sleep_duration: SleepDuration
        energy_level: EnergyLevel | None

`Rule`/`RuleEngine` are generic over `RuleContext` subtypes (`rule.py`,
`engine.py`), so a `Rule[ReadinessRuleContext]` can only ever be evaluated
against a `ReadinessRuleContext` — enforced by mypy, not by a runtime
`isinstance` check anywhere in this package.
"""


class RuleContext:
    """Marker base class for the input snapshot a `Rule` evaluates
    against. See the module docstring for why it declares no fields of its
    own — every concrete context is defined by the engine that needs it,
    not by this shared package.
    """
