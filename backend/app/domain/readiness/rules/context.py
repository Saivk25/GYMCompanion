"""`ReadinessRuleContext`: the `RuleContext` (`app.domain.rules`) subtype
every readiness rule in this package evaluates against.

Deliberately narrower than `app.domain.readiness.context.ReadinessContext`
— that type is a full read-model snapshot of a `Readiness` check-in
(identity, source, notes, every field), meant for "a future domain service
[to] consume everything it needs to know about one check-in." This type
carries only the six fields the five rules in this package actually read.
No `readiness_id`, no `user_id`, no `notes` — a rule has no use for them,
and "`ReadinessRuleContext` contains only the data required by readiness
rules" is this phase's own explicit instruction, not just a style
preference. The two types are also structurally distinct for a second
reason: `RuleContext` is the shared Rule Engine kernel's own extensibility
point (`app.domain.rules.context`), and coupling the aggregate's general
read model to that hierarchy would reach the wrong direction — the
Readiness aggregate should not need to know the Rule Engine exists.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.readiness.readiness import Readiness
from app.domain.readiness.value_objects import (
    EnergyLevel,
    HeartRateVariability,
    RestingHeartRate,
    SleepDuration,
    SorenessLevel,
    StressLevel,
)
from app.domain.rules.context import RuleContext


@dataclass(frozen=True, kw_only=True)
class ReadinessRuleContext(RuleContext):
    """One evaluation's worth of readiness data. Every field is optional,
    matching `Readiness`'s own fields — a check-in with only some data
    recorded is normal (`Readiness.record()` requires none of them), and
    each rule below is individually responsible for deciding what "no
    data for me" means (uniformly: pass, not fail — see each rule's own
    docstring)."""

    sleep_duration: SleepDuration | None = None
    energy_level: EnergyLevel | None = None
    stress_level: StressLevel | None = None
    soreness_level: SorenessLevel | None = None
    resting_heart_rate: RestingHeartRate | None = None
    heart_rate_variability: HeartRateVariability | None = None

    @classmethod
    def from_readiness(cls, readiness: Readiness) -> ReadinessRuleContext:
        """Builds a context from an already-loaded `Readiness` aggregate.
        Takes the aggregate itself, not a `ReadinessId` or a repository —
        this package declares no repository dependency of its own (per
        this phase's explicit "no repositories, no services" instruction);
        loading the `Readiness` first is a caller concern.
        """
        return cls(
            sleep_duration=readiness.sleep_duration,
            energy_level=readiness.energy_level,
            stress_level=readiness.stress_level,
            soreness_level=readiness.soreness_level,
            resting_heart_rate=readiness.resting_heart_rate,
            heart_rate_variability=readiness.heart_rate_variability,
        )
