"""`UpdateRecoveryMetricsCommand`: the input to
`UpdateRecoveryMetricsHandler`.

**`None` means "leave unchanged," the same convention
`Readiness.update_recovery_metrics()` itself already documents** — all
five fields (`energy_level`/`stress_level`/`soreness_level`/
`resting_heart_rate`/`heart_rate_variability`) are each independently
optional, matching the aggregate method's own signature exactly. A
command's job is to carry a caller's intent through to the aggregate
method it invokes unmodified; this command invents no meaning of its
own for `None` beyond what `Readiness.update_recovery_metrics()`
already defines.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.command import Command
from app.domain.readiness.identifiers import ReadinessId
from app.domain.readiness.value_objects import (
    EnergyLevel,
    HeartRateVariability,
    RestingHeartRate,
    SorenessLevel,
    StressLevel,
)
from app.domain.user.identifiers import UserId


@dataclass(frozen=True, kw_only=True)
class UpdateRecoveryMetricsCommand(Command):
    """Replace whichever recovery-metric fields are given on an existing
    Readiness check-in; a field left `None` keeps its current stored
    value.

    `requester_id` is the authenticated caller — see
    `app.application.readiness.queries.get_readiness.GetReadinessQuery`'s
    own module docstring for the full ownership-check reasoning, which
    applies identically here.
    """

    readiness_id: ReadinessId
    requester_id: UserId
    energy_level: EnergyLevel | None = None
    stress_level: StressLevel | None = None
    soreness_level: SorenessLevel | None = None
    resting_heart_rate: RestingHeartRate | None = None
    heart_rate_variability: HeartRateVariability | None = None
