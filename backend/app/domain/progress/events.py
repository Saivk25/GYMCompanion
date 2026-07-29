"""Domain events raised by the Progress aggregate.

Scoped to exactly the four events this increment's task named —
`ProgressRecorded`, `MeasurementsUpdated`, `BodyCompositionUpdated`,
`ProgressNotesUpdated` — the same "raise only what the aggregate's own
methods actually do" discipline every other aggregate's `events.py`
already follows.

The three `*Updated` events each carry the *full resulting state* of their
field group (every measurement/body-composition field currently on the
record, not just the ones that changed in this particular call) rather
than a diff — the same choice
`app.domain.workout_session.events.WorkoutSessionNotesUpdated` makes for
its own full-value-object payload: a downstream reader (Progress
Intelligence, not built yet) needs a coherent snapshot of "what is this
group now", not a partial delta it would have to reconstruct history to
make sense of.
"""

from dataclasses import dataclass

from app.domain.progress.enums import MeasurementUnit, ProgressSource
from app.domain.progress.identifiers import ProgressId
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
from app.domain.shared_kernel.events import DomainEvent
from app.domain.user.identifiers import UserId


@dataclass(frozen=True, kw_only=True)
class ProgressRecorded(DomainEvent):
    """A new Progress check-in was created via `Progress.record(...)`.
    Carries the identifying fields a first subscriber would need without
    re-fetching the aggregate; body-composition/measurement values are
    covered by `BodyCompositionUpdated`/`MeasurementsUpdated` when set,
    including when set as part of the same `record()` call — see
    `progress.py`'s class docstring.
    """

    progress_id: ProgressId
    user_id: UserId
    progress_date: ProgressDate
    unit: MeasurementUnit
    source: ProgressSource


@dataclass(frozen=True, kw_only=True)
class BodyCompositionUpdated(DomainEvent):
    """`Progress.update_body_composition(...)` changed one or more of
    `body_weight`/`body_fat_percentage`/`lean_body_mass`/`muscle_mass`.
    Carries the resulting value of all four (each still `None` if never
    set), not just the ones this call changed — see the module docstring.
    """

    progress_id: ProgressId
    user_id: UserId
    body_weight: BodyWeight | None
    body_fat_percentage: BodyFatPercentage | None
    lean_body_mass: LeanBodyMass | None
    muscle_mass: MuscleMass | None


@dataclass(frozen=True, kw_only=True)
class MeasurementsUpdated(DomainEvent):
    """`Progress.update_measurements(...)` changed one or more tape
    measurements. Carries the resulting value of all seven (each still
    `None` if never set), not just the ones this call changed — see the
    module docstring.
    """

    progress_id: ProgressId
    user_id: UserId
    waist: WaistMeasurement | None
    chest: ChestMeasurement | None
    hip: HipMeasurement | None
    arm: ArmMeasurement | None
    thigh: ThighMeasurement | None
    calf: CalfMeasurement | None
    neck: NeckMeasurement | None


@dataclass(frozen=True, kw_only=True)
class ProgressNotesUpdated(DomainEvent):
    """`Progress.update_notes(...)` replaced this record's notes. Carries
    the full new `notes`, the same choice
    `app.domain.workout_session.events.WorkoutSessionNotesUpdated` makes.
    """

    progress_id: ProgressId
    user_id: UserId
    notes: ProgressNotes
