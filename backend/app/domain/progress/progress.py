"""The Progress aggregate root.

The user's long-term fitness history: a canonical, point-in-time check-in
of body weight, body composition, and tape measurements. Domain Model &
Decision Engine Bible, Section 4.10's `Measurement` (Table 13, "a sibling
append-only log on the same review cadence" as `PhotoCheckin`) is the
closest analog, broadened here to cover body composition
(`BodyFatPercentage`/`LeanBodyMass`/`MuscleMass`) and two extra tape sites
(`CalfMeasurement`/`NeckMeasurement`) the Bible's own table doesn't name —
this increment's own scope, not an oversight (see each value object's own
docstring in `value_objects.py`).

This aggregate stores canonical progress information only. It does not
compute trends, streaks, personal records, or anything derived from a
series of records — that is Progress Intelligence's job (Bible Section
4.9/9.3: `Trend`, `PlateauEvent`, `Forecast`), a separate, not-yet-built
context that reads this aggregate's events, never the other way around.

Tenant-scoped like `Workout` and `WorkoutSession` (carries `user_id`) —
progress history is inherently personal.

On immutability: this task's own rule states "Progress records become
immutable after recording (future corrections should create new records
rather than mutate history)." Unlike `Workout`/`Exercise`/`WorkoutSession`,
`Progress` has no status enum and no lifecycle to gate mutation on — a
single check-in is a fact, not a multi-step workflow. `update_body_
composition()`, `update_measurements()`, and `update_notes()` are real,
unguarded mutating methods (this increment's own task names their events
explicitly, so they exist), intended for amending a record still being
actively assembled (e.g. a smart-scale sync arriving moments after a
manual weight entry for the same check-in). The stronger rule — never
mutate a *closed, historical* record; record a new one instead — is a
data-lifecycle policy this increment does not mechanize at the domain
layer, because nothing on `Progress` can distinguish "still being entered"
from "reviewed months ago" without inventing a status concept the task
didn't ask for. See `docs/adr/0010-progress-immutability-is-a-policy-not-a-guard.md`
for the full reasoning and what a future increment would need to add to
enforce this at the domain layer.
"""

from __future__ import annotations

from datetime import datetime

from app.domain.progress.enums import MeasurementUnit, ProgressSource
from app.domain.progress.events import (
    BodyCompositionUpdated,
    MeasurementsUpdated,
    ProgressNotesUpdated,
    ProgressRecorded,
)
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
from app.domain.shared_kernel.aggregate_root import AggregateRoot
from app.domain.shared_kernel.clock import Clock
from app.domain.shared_kernel.validation import ensure
from app.domain.user.identifiers import UserId


class Progress(AggregateRoot[ProgressId]):
    """The Progress aggregate. See the module docstring for scope and the
    ADR for the immutability-as-policy reasoning.

    Construct a brand-new record via the `record()` factory, never
    `Progress(...)` directly — the constructor is also used to rehydrate an
    existing record from a repository, where re-raising `ProgressRecorded`
    would be wrong.
    """

    def __init__(
        self,
        progress_id: ProgressId,
        *,
        user_id: UserId,
        progress_date: ProgressDate,
        unit: MeasurementUnit,
        source: ProgressSource,
        recorded_at: datetime,
        body_weight: BodyWeight | None = None,
        body_fat_percentage: BodyFatPercentage | None = None,
        lean_body_mass: LeanBodyMass | None = None,
        muscle_mass: MuscleMass | None = None,
        waist: WaistMeasurement | None = None,
        chest: ChestMeasurement | None = None,
        hip: HipMeasurement | None = None,
        arm: ArmMeasurement | None = None,
        thigh: ThighMeasurement | None = None,
        calf: CalfMeasurement | None = None,
        neck: NeckMeasurement | None = None,
        notes: ProgressNotes | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        super().__init__(progress_id)
        ensure(recorded_at.tzinfo is not None, "recorded_at must be timezone-aware")
        self._user_id = user_id
        self._progress_date = progress_date
        self._unit = unit
        self._source = source
        self._recorded_at = recorded_at
        self._body_weight = body_weight
        self._body_fat_percentage = body_fat_percentage
        self._lean_body_mass = lean_body_mass
        self._muscle_mass = muscle_mass
        self._waist = waist
        self._chest = chest
        self._hip = hip
        self._arm = arm
        self._thigh = thigh
        self._calf = calf
        self._neck = neck
        self._notes = notes if notes is not None else ProgressNotes()
        self._updated_at = updated_at

    @classmethod
    def record(
        cls,
        *,
        progress_id: ProgressId,
        user_id: UserId,
        progress_date: ProgressDate,
        unit: MeasurementUnit,
        source: ProgressSource,
        clock: Clock,
        body_weight: BodyWeight | None = None,
        body_fat_percentage: BodyFatPercentage | None = None,
        lean_body_mass: LeanBodyMass | None = None,
        muscle_mass: MuscleMass | None = None,
        waist: WaistMeasurement | None = None,
        chest: ChestMeasurement | None = None,
        hip: HipMeasurement | None = None,
        arm: ArmMeasurement | None = None,
        thigh: ThighMeasurement | None = None,
        calf: CalfMeasurement | None = None,
        neck: NeckMeasurement | None = None,
        notes: ProgressNotes | None = None,
    ) -> Progress:
        """Creates a brand-new Progress check-in and records
        `ProgressRecorded`. `progress_id` is generated by the caller
        (`ProgressId.generate()`) before calling this — the same
        convention every other aggregate's factory follows.

        Every body-composition/measurement field can be supplied here
        directly (the common case: a single check-in where everything was
        captured at once) or filled in afterward via `update_body_
        composition()`/`update_measurements()` — both are equally valid;
        see the class docstring for what "immutable after recording"
        does and doesn't mean here.
        """
        recorded_at = clock.now()
        progress = cls(
            progress_id,
            user_id=user_id,
            progress_date=progress_date,
            unit=unit,
            source=source,
            recorded_at=recorded_at,
            body_weight=body_weight,
            body_fat_percentage=body_fat_percentage,
            lean_body_mass=lean_body_mass,
            muscle_mass=muscle_mass,
            waist=waist,
            chest=chest,
            hip=hip,
            arm=arm,
            thigh=thigh,
            calf=calf,
            neck=neck,
            notes=notes,
        )
        progress.record_event(
            ProgressRecorded(
                occurred_at=recorded_at,
                progress_id=progress_id,
                user_id=user_id,
                progress_date=progress_date,
                unit=unit,
                source=source,
            )
        )
        return progress

    @property
    def user_id(self) -> UserId:
        return self._user_id

    @property
    def progress_date(self) -> ProgressDate:
        return self._progress_date

    @property
    def unit(self) -> MeasurementUnit:
        return self._unit

    @property
    def source(self) -> ProgressSource:
        return self._source

    @property
    def recorded_at(self) -> datetime:
        return self._recorded_at

    @property
    def body_weight(self) -> BodyWeight | None:
        return self._body_weight

    @property
    def body_fat_percentage(self) -> BodyFatPercentage | None:
        return self._body_fat_percentage

    @property
    def lean_body_mass(self) -> LeanBodyMass | None:
        return self._lean_body_mass

    @property
    def muscle_mass(self) -> MuscleMass | None:
        return self._muscle_mass

    @property
    def waist(self) -> WaistMeasurement | None:
        return self._waist

    @property
    def chest(self) -> ChestMeasurement | None:
        return self._chest

    @property
    def hip(self) -> HipMeasurement | None:
        return self._hip

    @property
    def arm(self) -> ArmMeasurement | None:
        return self._arm

    @property
    def thigh(self) -> ThighMeasurement | None:
        return self._thigh

    @property
    def calf(self) -> CalfMeasurement | None:
        return self._calf

    @property
    def neck(self) -> NeckMeasurement | None:
        return self._neck

    @property
    def notes(self) -> ProgressNotes:
        return self._notes

    @property
    def updated_at(self) -> datetime | None:
        return self._updated_at

    def update_body_composition(
        self,
        *,
        clock: Clock,
        body_weight: BodyWeight | None = None,
        body_fat_percentage: BodyFatPercentage | None = None,
        lean_body_mass: LeanBodyMass | None = None,
        muscle_mass: MuscleMass | None = None,
    ) -> None:
        """Replaces whichever body-composition fields are given (`None`
        means "leave unchanged", the same convention
        `app.domain.exercise.exercise.Exercise.update()` uses) and records
        one `BodyCompositionUpdated` carrying the resulting value of all
        four fields.
        """
        if body_weight is not None:
            self._body_weight = body_weight
        if body_fat_percentage is not None:
            self._body_fat_percentage = body_fat_percentage
        if lean_body_mass is not None:
            self._lean_body_mass = lean_body_mass
        if muscle_mass is not None:
            self._muscle_mass = muscle_mass
        self._updated_at = clock.now()
        self.record_event(
            BodyCompositionUpdated(
                occurred_at=self._updated_at,
                progress_id=self.id,
                user_id=self._user_id,
                body_weight=self._body_weight,
                body_fat_percentage=self._body_fat_percentage,
                lean_body_mass=self._lean_body_mass,
                muscle_mass=self._muscle_mass,
            )
        )

    def update_measurements(
        self,
        *,
        clock: Clock,
        waist: WaistMeasurement | None = None,
        chest: ChestMeasurement | None = None,
        hip: HipMeasurement | None = None,
        arm: ArmMeasurement | None = None,
        thigh: ThighMeasurement | None = None,
        calf: CalfMeasurement | None = None,
        neck: NeckMeasurement | None = None,
    ) -> None:
        """Replaces whichever tape measurements are given (`None` means
        "leave unchanged") and records one `MeasurementsUpdated` carrying
        the resulting value of all seven fields.
        """
        if waist is not None:
            self._waist = waist
        if chest is not None:
            self._chest = chest
        if hip is not None:
            self._hip = hip
        if arm is not None:
            self._arm = arm
        if thigh is not None:
            self._thigh = thigh
        if calf is not None:
            self._calf = calf
        if neck is not None:
            self._neck = neck
        self._updated_at = clock.now()
        self.record_event(
            MeasurementsUpdated(
                occurred_at=self._updated_at,
                progress_id=self.id,
                user_id=self._user_id,
                waist=self._waist,
                chest=self._chest,
                hip=self._hip,
                arm=self._arm,
                thigh=self._thigh,
                calf=self._calf,
                neck=self._neck,
            )
        )

    def update_notes(self, notes: ProgressNotes, *, clock: Clock) -> None:
        """Replaces this record's notes wholesale and records one
        `ProgressNotesUpdated`."""
        self._notes = notes
        self._updated_at = clock.now()
        self.record_event(
            ProgressNotesUpdated(
                occurred_at=self._updated_at,
                progress_id=self.id,
                user_id=self._user_id,
                notes=notes,
            )
        )
