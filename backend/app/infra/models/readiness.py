"""`ReadinessRow`: persistence row for the Readiness aggregate.

Tenant-scoped (`user_id` foreign key to `users`), same RLS shape as
`workouts`/`progress_records`/`nutrition_entries`. One row per logged
check-in. "One CheckIn per day" (Domain Model & Decision Engine Bible,
Section 4.8, Table 11) is explicitly not enforced at the domain layer (see
`readiness.py`'s own module docstring: "a single `Readiness` instance has no
visibility into any other instance for the same user/date") and is likewise
not enforced here — no unique constraint on `(user_id, readiness_date)` —
consistent with that documented, deliberate deferral; a future increment
that wants to enforce it would add a partial unique index and a decision on
how the application layer should react to a violation, not silently retrofit
one into this migration.
"""

import uuid
from datetime import date, datetime, timedelta

from sqlalchemy import CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TIMESTAMP, Date, Interval, Uuid

from app.infra.orm_base import Base

_SOURCES = ("manual", "wearable", "imported")


class ReadinessRow(Base):
    """Persistence row for the Readiness aggregate. See
    `app/infra/repositories/readiness_repository.py` for the translation
    to/from `app.domain.readiness.Readiness`.
    """

    __tablename__ = "readiness_checkins"
    __table_args__ = (
        CheckConstraint(f"source IS NULL OR source IN {_SOURCES}", name="valid_source"),
    )

    readiness_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.user_id"), nullable=False
    )
    readiness_date: Mapped[date] = mapped_column(Date(), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    source: Mapped[str | None] = mapped_column(nullable=True)

    sleep_duration: Mapped[timedelta | None] = mapped_column(Interval(), nullable=True)
    sleep_quality: Mapped[int | None] = mapped_column(nullable=True)
    energy_level: Mapped[int | None] = mapped_column(nullable=True)
    stress_level: Mapped[int | None] = mapped_column(nullable=True)
    soreness_level: Mapped[int | None] = mapped_column(nullable=True)
    resting_heart_rate: Mapped[float | None] = mapped_column(nullable=True)
    heart_rate_variability: Mapped[float | None] = mapped_column(nullable=True)

    notes: Mapped[str] = mapped_column(nullable=False, server_default="")
    updated_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
