"""`ExerciseRow`: persistence row for the Exercise aggregate.

No `user_id` column and no row-level security — `Exercise` is explicitly
not tenant-scoped (`app.domain.exercise.exercise`'s own module docstring:
"curated by the system/maintainer... shared/global, not per-user, every
`Exercise` is visible to every user"). This is the one table in this
package that deliberately breaks the "every table gets RLS" convention,
for the same reason the Architecture document's own multi-tenancy mandate
never claimed reference/catalog data needed tenant isolation in the first
place — there is no tenant to isolate it from.
"""

import uuid
from datetime import datetime

from sqlalchemy import ARRAY, CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TIMESTAMP, Uuid

from app.infra.orm_base import Base

_DIFFICULTIES = ("beginner", "intermediate", "advanced")
_STATUSES = ("active", "deprecated")
_MOVEMENT_PATTERNS = (
    "push",
    "pull",
    "hinge",
    "squat",
    "lunge",
    "carry",
    "rotation",
    "core",
    "cardio",
)


class ExerciseRow(Base):
    """Persistence row for the Exercise aggregate — the shared exercise
    catalog. See `app/infra/repositories/exercise_repository.py` for the
    translation to/from `app.domain.exercise.Exercise`.
    """

    __tablename__ = "exercises"
    __table_args__ = (
        CheckConstraint(f"difficulty IN {_DIFFICULTIES}", name="valid_difficulty"),
        CheckConstraint(f"status IN {_STATUSES}", name="valid_status"),
        CheckConstraint(f"movement_pattern IN {_MOVEMENT_PATTERNS}", name="valid_movement_pattern"),
    )

    exercise_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    movement_pattern: Mapped[str] = mapped_column(nullable=False)
    difficulty: Mapped[str] = mapped_column(nullable=False)
    instructions: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    description: Mapped[str | None] = mapped_column(nullable=True)
    primary_muscles: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, server_default="{}"
    )
    secondary_muscles: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, server_default="{}"
    )
    equipment_requirements: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, server_default="{}"
    )
    contraindication_tags: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, server_default="{}"
    )
    status: Mapped[str] = mapped_column(nullable=False, server_default="active")
    updated_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    deprecated_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
