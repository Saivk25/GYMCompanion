"""The Progress aggregate: Sprint 2's fifth real aggregate, built on the
Sprint 1 shared kernel (`app.domain.shared_kernel`) and following the same
pattern as `app.domain.user`, `app.domain.workout`, `app.domain.exercise`,
and `app.domain.workout_session`. Body & Media bounded context (Domain
Model & Decision Engine Bible, Section 3, Table 2), closest deep dive in
Section 4.10 (`Measurement`).

The user's canonical, long-term fitness history: body weight, body
composition, and tape measurements, recorded over time. Stores facts only
— no trend calculations, charts, personal records, strength progression,
volume calculations, analytics, or recommendations. Those belong to
Progress Intelligence (Bible Section 4.9/9.3), a separate, not-yet-built
context that reads this aggregate's events, never the reverse.

See `docs/adr/0010-progress-immutability-is-a-policy-not-a-guard.md` for
why "Progress records become immutable after recording" is documented
policy rather than a domain-layer-enforced guard in this increment.

Depends on nothing outside the Python standard library,
`app.domain.shared_kernel`, and `app.domain.user` (for the owning
`UserId`) — enforced by the same statically-checked rule as the rest of
`app/domain` (`tests/domain/test_import_boundaries.py`).
"""

from app.domain.progress.context import ProgressContext
from app.domain.progress.enums import MeasurementUnit, ProgressSource
from app.domain.progress.events import (
    BodyCompositionUpdated,
    MeasurementsUpdated,
    ProgressNotesUpdated,
    ProgressRecorded,
)
from app.domain.progress.identifiers import ProgressId
from app.domain.progress.progress import Progress
from app.domain.progress.repository import ProgressRepository
from app.domain.progress.value_objects import (
    ArmMeasurement,
    BodyFatPercentage,
    BodyWeight,
    CalfMeasurement,
    ChestMeasurement,
    HipMeasurement,
    LeanBodyMass,
    MuscleMass,
    NeckMeasurement,
    ProgressDate,
    ProgressNotes,
    ThighMeasurement,
    WaistMeasurement,
)

__all__ = [
    "ArmMeasurement",
    "BodyCompositionUpdated",
    "BodyFatPercentage",
    "BodyWeight",
    "CalfMeasurement",
    "ChestMeasurement",
    "HipMeasurement",
    "LeanBodyMass",
    "MeasurementUnit",
    "MeasurementsUpdated",
    "MuscleMass",
    "NeckMeasurement",
    "Progress",
    "ProgressContext",
    "ProgressDate",
    "ProgressId",
    "ProgressNotes",
    "ProgressNotesUpdated",
    "ProgressRecorded",
    "ProgressRepository",
    "ProgressSource",
    "ThighMeasurement",
    "WaistMeasurement",
]
