"""`NutritionRow`: persistence row for the Nutrition aggregate.

Tenant-scoped (`user_id` foreign key to `users`), same RLS shape as
`workouts`/`progress_records`. One row per logged entry, not a daily
rollup — see `docs/adr/0011-nutrition-is-a-per-entry-log-not-a-daily-rollup.md`
— so `nutrition_date` is deliberately not unique per user; a user may log
many entries on the same date. `meal_type`/`source` are nullable (unlike
`ProgressRow.unit`/`source`, which are required) because they are optional
on the aggregate itself.
"""

import uuid
from datetime import date, datetime

from sqlalchemy import CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TIMESTAMP, Date, Uuid

from app.infra.orm_base import Base

_MEAL_TYPES = ("breakfast", "lunch", "dinner", "snack")
_SOURCES = ("manual", "barcode", "import")


class NutritionRow(Base):
    """Persistence row for the Nutrition aggregate. See
    `app/infra/repositories/nutrition_repository.py` for the translation
    to/from `app.domain.nutrition.Nutrition`.
    """

    __tablename__ = "nutrition_entries"
    __table_args__ = (
        CheckConstraint(f"meal_type IS NULL OR meal_type IN {_MEAL_TYPES}", name="valid_meal_type"),
        CheckConstraint(f"source IS NULL OR source IN {_SOURCES}", name="valid_source"),
    )

    nutrition_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.user_id"), nullable=False
    )
    nutrition_date: Mapped[date] = mapped_column(Date(), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    meal_type: Mapped[str | None] = mapped_column(nullable=True)
    source: Mapped[str | None] = mapped_column(nullable=True)

    calories: Mapped[float | None] = mapped_column(nullable=True)
    protein: Mapped[float | None] = mapped_column(nullable=True)
    carbohydrates: Mapped[float | None] = mapped_column(nullable=True)
    fat: Mapped[float | None] = mapped_column(nullable=True)
    fiber: Mapped[float | None] = mapped_column(nullable=True)
    sugar: Mapped[float | None] = mapped_column(nullable=True)
    water_intake: Mapped[float | None] = mapped_column(nullable=True)

    notes: Mapped[str] = mapped_column(nullable=False, server_default="")
    updated_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
