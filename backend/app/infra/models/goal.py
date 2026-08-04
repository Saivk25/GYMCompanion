"""`GoalRow`: persistence row for the Goal aggregate.

Tenant-scoped (`user_id` foreign key to `users`), same RLS shape as
`workouts`. `status` defaults to `active` — every `Goal` is created directly
`Active` (see `goal.py`'s own module docstring) — and its CHECK constraint
includes `expired` even though nothing in this increment's application or
domain code ever writes that value, for the same reason `GoalStatus.EXPIRED`
exists on the enum itself: a rehydrated row must never violate the
constraint that was defined for the type it maps, whether or not any
current code path produces that value (see
`docs/adr/0012-goal-lifecycle-and-expired-with-no-transition.md`).
"""

import uuid
from datetime import date, datetime

from sqlalchemy import CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TIMESTAMP, Date, Uuid

from app.infra.orm_base import Base

_GOAL_TYPES = (
    "lose_fat",
    "gain_muscle",
    "maintain",
    "strength",
    "endurance",
    "general_health",
)
_STATUSES = ("active", "completed", "cancelled", "expired")


class GoalRow(Base):
    """Persistence row for the Goal aggregate. See
    `app/infra/repositories/goal_repository.py` for the translation to/from
    `app.domain.goal.Goal`.
    """

    __tablename__ = "goals"
    __table_args__ = (
        CheckConstraint(f"goal_type IN {_GOAL_TYPES}", name="valid_goal_type"),
        CheckConstraint(f"status IN {_STATUSES}", name="valid_status"),
    )

    goal_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.user_id"), nullable=False
    )
    goal_type: Mapped[str] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    target_date: Mapped[date] = mapped_column(Date(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(nullable=False, server_default="active")

    description: Mapped[str | None] = mapped_column(nullable=True)
    target_weight: Mapped[float | None] = mapped_column(nullable=True)
    target_body_fat: Mapped[float | None] = mapped_column(nullable=True)
    target_strength: Mapped[float | None] = mapped_column(nullable=True)
    priority: Mapped[int | None] = mapped_column(nullable=True)
    notes: Mapped[str] = mapped_column(nullable=False, server_default="")

    updated_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
