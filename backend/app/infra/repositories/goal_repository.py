"""`GoalSqlRepository`: the SQLAlchemy-backed implementation of
`app.domain.goal.repository.GoalRepository`.

See `workout_repository.py`'s module docstring for the tenant-scoping shape
this repository follows.
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select

from app.domain.goal.enums import GoalStatus, GoalType
from app.domain.goal.goal import Goal
from app.domain.goal.identifiers import GoalId
from app.domain.goal.repository import GoalRepository
from app.domain.goal.value_objects import (
    GoalDescription,
    GoalName,
    GoalNotes,
    Priority,
    TargetBodyFat,
    TargetDate,
    TargetStrength,
    TargetWeight,
)
from app.domain.user.identifiers import UserId
from app.infra.database import tenant_scope
from app.infra.models.goal import GoalRow
from app.infra.repositories._tracking import TrackingRepository


class GoalSqlRepository(GoalRepository, TrackingRepository[Goal, GoalId, GoalRow]):
    """Postgres-backed `GoalRepository`. See the module docstring for the
    tenant-scoping shape."""

    def get(self, entity_id: GoalId) -> Goal | None:
        row = self._session.get(GoalRow, entity_id.value)
        if row is None:
            return None
        goal = _to_domain(row)
        self._track(entity_id, goal, row)
        return goal

    def add(self, aggregate: Goal) -> None:
        with tenant_scope(self._session, str(aggregate.user_id)):
            row = GoalRow(goal_id=aggregate.id.value, user_id=aggregate.user_id.value)
            self._apply_to_row(aggregate, row)
            self._session.add(row)
        self._track(aggregate.id, aggregate, row)

    def remove(self, aggregate: Goal) -> None:
        with tenant_scope(self._session, str(aggregate.user_id)):
            row = self._session.get(GoalRow, aggregate.id.value)
            if row is not None:
                self._session.delete(row)
        self._untrack(aggregate.id)

    def list_by_user(self, user_id: UserId) -> Sequence[Goal]:
        with tenant_scope(self._session, str(user_id)):
            rows = self._session.scalars(
                select(GoalRow).where(GoalRow.user_id == user_id.value)
            ).all()
        goals = []
        for row in rows:
            goal = _to_domain(row)
            self._track(goal.id, goal, row)
            goals.append(goal)
        return goals

    def _apply_to_row(self, aggregate: Goal, row: GoalRow) -> None:
        row.goal_type = aggregate.goal_type.value
        row.name = aggregate.name.value
        row.target_date = aggregate.target_date.value
        row.status = aggregate.status.value
        row.description = aggregate.description.value if aggregate.description is not None else None
        row.target_weight = (
            aggregate.target_weight.value if aggregate.target_weight is not None else None
        )
        row.target_body_fat = (
            aggregate.target_body_fat.value if aggregate.target_body_fat is not None else None
        )
        row.target_strength = (
            aggregate.target_strength.value if aggregate.target_strength is not None else None
        )
        row.priority = aggregate.priority.value if aggregate.priority is not None else None
        row.notes = aggregate.notes.value
        row.updated_at = aggregate.updated_at
        row.completed_at = aggregate.completed_at
        row.cancelled_at = aggregate.cancelled_at


def _to_domain(row: GoalRow) -> Goal:
    return Goal(
        GoalId(row.goal_id),
        user_id=UserId(row.user_id),
        goal_type=GoalType(row.goal_type),
        name=GoalName(row.name),
        target_date=TargetDate(row.target_date),
        created_at=row.created_at,
        description=GoalDescription(row.description) if row.description is not None else None,
        target_weight=TargetWeight(row.target_weight) if row.target_weight is not None else None,
        target_body_fat=(
            TargetBodyFat(row.target_body_fat) if row.target_body_fat is not None else None
        ),
        target_strength=(
            TargetStrength(row.target_strength) if row.target_strength is not None else None
        ),
        priority=Priority(row.priority) if row.priority is not None else None,
        notes=GoalNotes(row.notes),
        status=GoalStatus(row.status),
        updated_at=row.updated_at,
        completed_at=row.completed_at,
        cancelled_at=row.cancelled_at,
    )
