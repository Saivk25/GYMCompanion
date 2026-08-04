"""`WorkoutSessionRow`/`ExercisePerformanceRow`/`ExerciseSetRow`: persistence
rows for the WorkoutSession aggregate and its two owned child objects.

Per `docs/adr/0009-exercise-performance-owned-entity.md`, `ExercisePerformance`
(an `Entity`) and `ExerciseSet` (a `ValueObject`) are not separate aggregates
and have no repository of their own — they persist as child tables of
`workout_sessions`, mapped/reconstructed entirely within
`app/infra/repositories/workout_session_repository.py`. All three tables are
tenant-scoped: `user_id` is denormalized onto the two child tables (rather
than requiring a join back to `workout_sessions` to know whose row it is) so
every table can carry its own `USING (user_id::text = current_setting(
'app.current_user_id', true))` RLS policy independently, the same "every
table gets RLS" convention `workouts` already follows.

`ExercisePerformance.sets` and `WorkoutSession.exercise_performances` are
ordered tuples with no explicit domain-level ordering field — the domain
only guarantees "insertion order == read order" because sets/performances
are append-only, never reordered (see each class's own docstring). SQL rows
have no inherent order, so `ExercisePerformanceRow` carries a `sequence`
column — populated by the repository from each performance's position in
the tuple at write time, and used to `ORDER BY` on read — purely an infra
concern for reconstructing the domain's append-order guarantee; nothing in
`app.domain` knows this column exists. `ExerciseSetRow` needs no equivalent:
`set_number` is already the set's own natural, unique ordering key within a
performance (see `exercise_set.py`'s module docstring), so ordering by it
recovers the same order sets were logged in.
"""

import uuid
from datetime import date, datetime, timedelta

from sqlalchemy import CheckConstraint, ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TIMESTAMP, Date, Interval, Uuid

from app.infra.orm_base import Base

_SESSION_STATUSES = ("planned", "active", "completed", "abandoned")


class WorkoutSessionRow(Base):
    """Persistence row for the WorkoutSession aggregate root. See
    `app/infra/repositories/workout_session_repository.py` for the
    translation to/from `app.domain.workout_session.WorkoutSession`.
    """

    __tablename__ = "workout_sessions"
    __table_args__ = (CheckConstraint(f"status IN {_SESSION_STATUSES}", name="valid_status"),)

    session_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    workout_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("workouts.workout_id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.user_id"), nullable=False
    )
    session_date: Mapped[date] = mapped_column(Date(), nullable=False)
    planned_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(nullable=False, server_default="planned")
    notes: Mapped[str] = mapped_column(nullable=False, server_default="")
    duration: Mapped[timedelta | None] = mapped_column(Interval(), nullable=True)
    completion_percentage: Mapped[float | None] = mapped_column(nullable=True)
    rating: Mapped[int | None] = mapped_column(nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    abandoned_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)


class ExercisePerformanceRow(Base):
    """Persistence row for the `ExercisePerformance` entity owned by
    `WorkoutSession`. See the module docstring for the `sequence` column.
    """

    __tablename__ = "exercise_performances"

    performance_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("workout_sessions.session_id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.user_id"), nullable=False
    )
    exercise_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("exercises.exercise_id"), nullable=False
    )
    sequence: Mapped[int] = mapped_column(nullable=False)
    notes: Mapped[str] = mapped_column(nullable=False, server_default="")


class ExerciseSetRow(Base):
    """Persistence row for one `ExerciseSet` value object logged on an
    `ExercisePerformance`. Composite primary key `(performance_id,
    set_number)` mirrors the domain's own uniqueness rule — `ExercisePerformance.
    add_set()` already rejects a duplicate `set_number` within one
    performance (see `exercise_performance.py`), so no synthetic id column
    is needed; the natural key is unique by construction.
    """

    __tablename__ = "exercise_sets"
    __table_args__ = (
        ForeignKeyConstraint(
            ["performance_id"],
            ["exercise_performances.performance_id"],
            name="fk_exercise_sets_performance_id_exercise_performances",
        ),
    )

    performance_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    set_number: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.user_id"), nullable=False
    )
    weight: Mapped[float] = mapped_column(nullable=False)
    reps: Mapped[int] = mapped_column(nullable=False)
    rpe: Mapped[int] = mapped_column(nullable=False)
    completed: Mapped[bool] = mapped_column(nullable=False, server_default="false")
