"""`ReadinessDTO`: the read-only projection of a `Readiness` aggregate
returned to whatever calls a Readiness query handler.

Not the same type as `app.domain.readiness.context.ReadinessContext` —
identical reasoning to `NutritionDTO`'s own module docstring
(`app.application.nutrition.dto.nutrition_dto`): `ReadinessContext` is
scoped to a future domain service ("a future domain service [to]
consume everything it needs to know about one check-in" — that module's
own docstring), one-directional, and never crosses the Application
Layer boundary; `ReadinessDTO` is this layer's own read projection for
`GetReadinessHandler`/`ListReadinessHandler`, a different consumer with
different reasons to change independently. See `docs/adr/0027-
readiness-application-use-cases.md`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from app.domain.readiness.enums import ReadinessSource
from app.domain.readiness.identifiers import ReadinessId
from app.domain.readiness.value_objects import (
    EnergyLevel,
    HeartRateVariability,
    ReadinessDate,
    RecoveryNotes,
    RestingHeartRate,
    SleepDuration,
    SleepQuality,
    SorenessLevel,
    StressLevel,
)
from app.domain.user.identifiers import UserId

if TYPE_CHECKING:
    # Import only for the type checker — see UserDTO's identical note
    # for why this avoids a real circular import at module load time.
    from app.domain.readiness.readiness import Readiness


@dataclass(frozen=True, kw_only=True)
class ReadinessDTO:
    """An immutable, read-only snapshot of one `Readiness` check-in,
    taken at query time."""

    readiness_id: ReadinessId
    user_id: UserId
    readiness_date: ReadinessDate
    recorded_at: datetime
    source: ReadinessSource | None
    sleep_duration: SleepDuration | None
    sleep_quality: SleepQuality | None
    energy_level: EnergyLevel | None
    stress_level: StressLevel | None
    soreness_level: SorenessLevel | None
    resting_heart_rate: RestingHeartRate | None
    heart_rate_variability: HeartRateVariability | None
    notes: RecoveryNotes
    updated_at: datetime | None

    @classmethod
    def from_readiness(cls, readiness: Readiness) -> ReadinessDTO:
        """Builds a DTO from a live `Readiness` aggregate. One-
        directional on purpose, mirroring `NutritionDTO.from_nutrition` —
        `Readiness` never depends on this type.
        """
        return cls(
            readiness_id=readiness.id,
            user_id=readiness.user_id,
            readiness_date=readiness.readiness_date,
            recorded_at=readiness.recorded_at,
            source=readiness.source,
            sleep_duration=readiness.sleep_duration,
            sleep_quality=readiness.sleep_quality,
            energy_level=readiness.energy_level,
            stress_level=readiness.stress_level,
            soreness_level=readiness.soreness_level,
            resting_heart_rate=readiness.resting_heart_rate,
            heart_rate_variability=readiness.heart_rate_variability,
            notes=readiness.notes,
            updated_at=readiness.updated_at,
        )
