"""`ReadinessContext`: a read-only snapshot of a Readiness entry for domain
services.

Same purpose as `UserContext`, `WorkoutContext`, `ExerciseContext`,
`WorkoutSessionContext`, `ProgressContext`, and `NutritionContext`: lets a
future domain service — `RecoveryState` derivation, the Safety Rule
Engine, none built yet — consume everything it needs to know about one
check-in in a single immutable value.
"""

from __future__ import annotations

from dataclasses import dataclass
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
from app.domain.shared_kernel.value_object import ValueObject
from app.domain.user.identifiers import UserId

if TYPE_CHECKING:
    # Import only for the type checker — see UserContext's identical note
    # for why this avoids a real circular import at module load time.
    from app.domain.readiness.readiness import Readiness


@dataclass(frozen=True, kw_only=True)
class ReadinessContext(ValueObject):
    """An immutable snapshot of one Readiness check-in, taken at a point
    in time."""

    readiness_id: ReadinessId
    user_id: UserId
    readiness_date: ReadinessDate
    source: ReadinessSource | None
    sleep_duration: SleepDuration | None
    sleep_quality: SleepQuality | None
    energy_level: EnergyLevel | None
    stress_level: StressLevel | None
    soreness_level: SorenessLevel | None
    resting_heart_rate: RestingHeartRate | None
    heart_rate_variability: HeartRateVariability | None
    notes: RecoveryNotes

    @classmethod
    def from_readiness(cls, readiness: Readiness) -> ReadinessContext:
        """Builds a snapshot from a live `Readiness` aggregate. One-
        directional on purpose: `Readiness` does not know this type
        exists.
        """
        return cls(
            readiness_id=readiness.id,
            user_id=readiness.user_id,
            readiness_date=readiness.readiness_date,
            source=readiness.source,
            sleep_duration=readiness.sleep_duration,
            sleep_quality=readiness.sleep_quality,
            energy_level=readiness.energy_level,
            stress_level=readiness.stress_level,
            soreness_level=readiness.soreness_level,
            resting_heart_rate=readiness.resting_heart_rate,
            heart_rate_variability=readiness.heart_rate_variability,
            notes=readiness.notes,
        )
