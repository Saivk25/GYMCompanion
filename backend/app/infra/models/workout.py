"""`WorkoutRow`: persistence row for the Workout aggregate.

Tenant-scoped (`user_id` foreign key to `users`) — row-level security is
enabled and forced by this table's creating migration, following the
"child of an already-authenticated tenant" policy shape the original
`users` migration documents for every table after it: `USING (user_id::
text = current_setting('app.current_user_id', true))`, no `WITH CHECK`
override.
"""

import uuid
from datetime import date, datetime, timedelta

from sqlalchemy import CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TIMESTAMP, Date, Interval, Uuid

from app.infra.orm_base import Base

_STATUSES = ("planned", "in_progress", "completed", "cancelled")


class WorkoutRow(Base):
    """Persistence row for the Workout aggregate. See
    `app/infra/repositories/workout_repository.py` for the translation
    to/from `app.domain.workout.Workout`.
    """

    __tablename__ = "workouts"
    __table_args__ = (CheckConstraint(f"status IN {_STATUSES}", name="valid_status"),)

    workout_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.user_id"), nullable=False
    )
    name: Mapped[str] = mapped_column(nullable=False)
    planned_date: Mapped[date] = mapped_column(Date(), nullable=False)
    planned_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(nullable=False, server_default="planned")
    goal: Mapped[str | None] = mapped_column(nullable=True)
    notes: Mapped[str | None] = mapped_column(nullable=True)
    duration: Mapped[timedelta | None] = mapped_column(Interval(), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
