"""`ProgressSqlRepository`: the SQLAlchemy-backed implementation of
`app.domain.progress.repository.ProgressRepository`.

See `workout_repository.py`'s module docstring for the tenant-scoping shape
this repository follows (`add()`/`remove()`/`list_by_user()` self-scope from
a known `user_id`; `get()` trusts the caller to have already opened
`tenant_scope` on the session).
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select

from app.domain.progress.enums import MeasurementUnit, ProgressSource
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
from app.domain.user.identifiers import UserId
from app.infra.database import tenant_scope
from app.infra.models.progress import ProgressRow
from app.infra.repositories._tracking import TrackingRepository


class ProgressSqlRepository(
    ProgressRepository, TrackingRepository[Progress, ProgressId, ProgressRow]
):
    """Postgres-backed `ProgressRepository`. See the module docstring for
    the tenant-scoping shape."""

    def get(self, entity_id: ProgressId) -> Progress | None:
        row = self._session.get(ProgressRow, entity_id.value)
        if row is None:
            return None
        progress = _to_domain(row)
        self._track(entity_id, progress, row)
        return progress

    def add(self, aggregate: Progress) -> None:
        with tenant_scope(self._session, str(aggregate.user_id)):
            row = ProgressRow(progress_id=aggregate.id.value, user_id=aggregate.user_id.value)
            self._apply_to_row(aggregate, row)
            self._session.add(row)
        self._track(aggregate.id, aggregate, row)

    def remove(self, aggregate: Progress) -> None:
        with tenant_scope(self._session, str(aggregate.user_id)):
            row = self._session.get(ProgressRow, aggregate.id.value)
            if row is not None:
                self._session.delete(row)
        self._untrack(aggregate.id)

    def list_by_user(self, user_id: UserId) -> Sequence[Progress]:
        with tenant_scope(self._session, str(user_id)):
            rows = self._session.scalars(
                select(ProgressRow).where(ProgressRow.user_id == user_id.value)
            ).all()
        records = []
        for row in rows:
            progress = _to_domain(row)
            self._track(progress.id, progress, row)
            records.append(progress)
        return records

    def _apply_to_row(self, aggregate: Progress, row: ProgressRow) -> None:
        row.progress_date = aggregate.progress_date.value
        row.unit = aggregate.unit.value
        row.source = aggregate.source.value
        row.body_weight = aggregate.body_weight.value if aggregate.body_weight is not None else None
        row.body_fat_percentage = (
            aggregate.body_fat_percentage.value
            if aggregate.body_fat_percentage is not None
            else None
        )
        row.lean_body_mass = (
            aggregate.lean_body_mass.value if aggregate.lean_body_mass is not None else None
        )
        row.muscle_mass = aggregate.muscle_mass.value if aggregate.muscle_mass is not None else None
        row.waist = aggregate.waist.value if aggregate.waist is not None else None
        row.chest = aggregate.chest.value if aggregate.chest is not None else None
        row.hip = aggregate.hip.value if aggregate.hip is not None else None
        row.arm = aggregate.arm.value if aggregate.arm is not None else None
        row.thigh = aggregate.thigh.value if aggregate.thigh is not None else None
        row.calf = aggregate.calf.value if aggregate.calf is not None else None
        row.neck = aggregate.neck.value if aggregate.neck is not None else None
        row.notes = aggregate.notes.value
        row.updated_at = aggregate.updated_at


def _to_domain(row: ProgressRow) -> Progress:
    return Progress(
        ProgressId(row.progress_id),
        user_id=UserId(row.user_id),
        progress_date=ProgressDate(row.progress_date),
        unit=MeasurementUnit(row.unit),
        source=ProgressSource(row.source),
        recorded_at=row.recorded_at,
        body_weight=BodyWeight(row.body_weight) if row.body_weight is not None else None,
        body_fat_percentage=(
            BodyFatPercentage(row.body_fat_percentage)
            if row.body_fat_percentage is not None
            else None
        ),
        lean_body_mass=LeanBodyMass(row.lean_body_mass) if row.lean_body_mass is not None else None,
        muscle_mass=MuscleMass(row.muscle_mass) if row.muscle_mass is not None else None,
        waist=WaistMeasurement(row.waist) if row.waist is not None else None,
        chest=ChestMeasurement(row.chest) if row.chest is not None else None,
        hip=HipMeasurement(row.hip) if row.hip is not None else None,
        arm=ArmMeasurement(row.arm) if row.arm is not None else None,
        thigh=ThighMeasurement(row.thigh) if row.thigh is not None else None,
        calf=CalfMeasurement(row.calf) if row.calf is not None else None,
        neck=NeckMeasurement(row.neck) if row.neck is not None else None,
        notes=ProgressNotes(row.notes),
        updated_at=row.updated_at,
    )
