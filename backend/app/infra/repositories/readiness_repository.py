"""`ReadinessSqlRepository`: the SQLAlchemy-backed implementation of
`app.domain.readiness.repository.ReadinessRepository`.

See `workout_repository.py`'s module docstring for the tenant-scoping shape
this repository follows.
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select

from app.domain.readiness.enums import ReadinessSource
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
from app.domain.user.identifiers import UserId
from app.infra.database import tenant_scope
from app.infra.models.readiness import ReadinessRow
from app.infra.repositories._tracking import TrackingRepository


class ReadinessSqlRepository(
    ReadinessRepository, TrackingRepository[Readiness, ReadinessId, ReadinessRow]
):
    """Postgres-backed `ReadinessRepository`. See the module docstring for
    the tenant-scoping shape."""

    def get(self, entity_id: ReadinessId) -> Readiness | None:
        row = self._session.get(ReadinessRow, entity_id.value)
        if row is None:
            return None
        readiness = _to_domain(row)
        self._track(entity_id, readiness, row)
        return readiness

    def add(self, aggregate: Readiness) -> None:
        with tenant_scope(self._session, str(aggregate.user_id)):
            row = ReadinessRow(readiness_id=aggregate.id.value, user_id=aggregate.user_id.value)
            self._apply_to_row(aggregate, row)
            self._session.add(row)
        self._track(aggregate.id, aggregate, row)

    def remove(self, aggregate: Readiness) -> None:
        with tenant_scope(self._session, str(aggregate.user_id)):
            row = self._session.get(ReadinessRow, aggregate.id.value)
            if row is not None:
                self._session.delete(row)
        self._untrack(aggregate.id)

    def list_by_user(self, user_id: UserId) -> Sequence[Readiness]:
        with tenant_scope(self._session, str(user_id)):
            rows = self._session.scalars(
                select(ReadinessRow).where(ReadinessRow.user_id == user_id.value)
            ).all()
        checkins = []
        for row in rows:
            readiness = _to_domain(row)
            self._track(readiness.id, readiness, row)
            checkins.append(readiness)
        return checkins

    def _apply_to_row(self, aggregate: Readiness, row: ReadinessRow) -> None:
        row.readiness_date = aggregate.readiness_date.value
        row.source = aggregate.source.value if aggregate.source is not None else None
        row.sleep_duration = (
            aggregate.sleep_duration.value if aggregate.sleep_duration is not None else None
        )
        row.sleep_quality = (
            aggregate.sleep_quality.value if aggregate.sleep_quality is not None else None
        )
        row.energy_level = (
            aggregate.energy_level.value if aggregate.energy_level is not None else None
        )
        row.stress_level = (
            aggregate.stress_level.value if aggregate.stress_level is not None else None
        )
        row.soreness_level = (
            aggregate.soreness_level.value if aggregate.soreness_level is not None else None
        )
        row.resting_heart_rate = (
            aggregate.resting_heart_rate.value if aggregate.resting_heart_rate is not None else None
        )
        row.heart_rate_variability = (
            aggregate.heart_rate_variability.value
            if aggregate.heart_rate_variability is not None
            else None
        )
        row.notes = aggregate.notes.value
        row.updated_at = aggregate.updated_at


def _to_domain(row: ReadinessRow) -> Readiness:
    return Readiness(
        ReadinessId(row.readiness_id),
        user_id=UserId(row.user_id),
        readiness_date=ReadinessDate(row.readiness_date),
        recorded_at=row.recorded_at,
        source=ReadinessSource(row.source) if row.source is not None else None,
        sleep_duration=SleepDuration(row.sleep_duration)
        if row.sleep_duration is not None
        else None,
        sleep_quality=SleepQuality(row.sleep_quality) if row.sleep_quality is not None else None,
        energy_level=EnergyLevel(row.energy_level) if row.energy_level is not None else None,
        stress_level=StressLevel(row.stress_level) if row.stress_level is not None else None,
        soreness_level=SorenessLevel(row.soreness_level)
        if row.soreness_level is not None
        else None,
        resting_heart_rate=(
            RestingHeartRate(row.resting_heart_rate) if row.resting_heart_rate is not None else None
        ),
        heart_rate_variability=(
            HeartRateVariability(row.heart_rate_variability)
            if row.heart_rate_variability is not None
            else None
        ),
        notes=RecoveryNotes(row.notes),
        updated_at=row.updated_at,
    )
