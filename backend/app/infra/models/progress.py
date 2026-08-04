"""`ProgressRow`: persistence row for the Progress aggregate.

Tenant-scoped (`user_id` foreign key to `users`), same RLS shape as
`workouts`. Flat and wide: every body-composition/measurement field is its
own nullable column — `Progress` has no nested entities and every value
object on it (`BodyWeight`, `WaistMeasurement`, etc.) is a single float, so
there is no structural mapping work here beyond "one column per optional
field," unlike `WorkoutSession`.
"""

import uuid
from datetime import date, datetime

from sqlalchemy import CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TIMESTAMP, Date, Uuid

from app.infra.orm_base import Base

_UNITS = ("metric", "imperial")
_SOURCES = ("manual", "smart_scale", "calculated")


class ProgressRow(Base):
    """Persistence row for the Progress aggregate. See
    `app/infra/repositories/progress_repository.py` for the translation
    to/from `app.domain.progress.Progress`.
    """

    __tablename__ = "progress_records"
    __table_args__ = (
        CheckConstraint(f"unit IN {_UNITS}", name="valid_unit"),
        CheckConstraint(f"source IN {_SOURCES}", name="valid_source"),
    )

    progress_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.user_id"), nullable=False
    )
    progress_date: Mapped[date] = mapped_column(Date(), nullable=False)
    unit: Mapped[str] = mapped_column(nullable=False)
    source: Mapped[str] = mapped_column(nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)

    body_weight: Mapped[float | None] = mapped_column(nullable=True)
    body_fat_percentage: Mapped[float | None] = mapped_column(nullable=True)
    lean_body_mass: Mapped[float | None] = mapped_column(nullable=True)
    muscle_mass: Mapped[float | None] = mapped_column(nullable=True)
    waist: Mapped[float | None] = mapped_column(nullable=True)
    chest: Mapped[float | None] = mapped_column(nullable=True)
    hip: Mapped[float | None] = mapped_column(nullable=True)
    arm: Mapped[float | None] = mapped_column(nullable=True)
    thigh: Mapped[float | None] = mapped_column(nullable=True)
    calf: Mapped[float | None] = mapped_column(nullable=True)
    neck: Mapped[float | None] = mapped_column(nullable=True)

    notes: Mapped[str] = mapped_column(nullable=False, server_default="")
    updated_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
