"""The Readiness aggregate: Sprint 2's seventh real aggregate, built on the
Sprint 1 shared kernel (`app.domain.shared_kernel`) and following the same
pattern as `app.domain.user`, `app.domain.workout`, `app.domain.exercise`,
`app.domain.workout_session`, `app.domain.progress`, and
`app.domain.nutrition`. Recovery & Safety bounded context (Domain Model &
Decision Engine Bible, Section 3, Table 2), closest deep dive in Section
4.8 (`ReadinessCheckIn`).

The canonical record of a user's daily recovery inputs: sleep, subjective
energy/stress/soreness, resting heart rate, and heart rate variability.
Stores observations only — no readiness score, recovery score, deload
recommendations, fatigue calculations, or workout recommendations. Those
belong to `RecoveryState` and the Safety Rule Engine, neither built yet.

Depends on nothing outside the Python standard library,
`app.domain.shared_kernel`, and `app.domain.user` (for the owning
`UserId`) — enforced by the same statically-checked rule as the rest of
`app/domain` (`tests/domain/test_import_boundaries.py`).
"""

from app.domain.readiness.context import ReadinessContext
from app.domain.readiness.enums import ReadinessSource
from app.domain.readiness.events import (
    ReadinessRecorded,
    RecoveryMetricsUpdated,
    RecoveryNotesUpdated,
    SleepUpdated,
)
from app.domain.readiness.identifiers import ReadinessId
from app.domain.readiness.readiness import Readiness
from app.domain.readiness.repository import ReadinessRepository
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

__all__ = [
    "EnergyLevel",
    "HeartRateVariability",
    "Readiness",
    "ReadinessContext",
    "ReadinessDate",
    "ReadinessId",
    "ReadinessRecorded",
    "ReadinessRepository",
    "ReadinessSource",
    "RecoveryMetricsUpdated",
    "RecoveryNotes",
    "RecoveryNotesUpdated",
    "RestingHeartRate",
    "SleepDuration",
    "SleepQuality",
    "SleepUpdated",
    "SorenessLevel",
    "StressLevel",
]
