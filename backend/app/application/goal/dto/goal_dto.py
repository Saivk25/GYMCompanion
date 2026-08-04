"""`GoalDTO`: the read-only projection of a `Goal` aggregate returned to
whatever calls a Goal query handler.

Not the same type as `app.domain.goal.context.GoalContext` — identical
reasoning to `ReadinessDTO`'s own module docstring
(`app.application.readiness.dto.readiness_dto`): `GoalContext` is scoped
to a future domain service ("lets a future domain service... consume
everything it needs to know about one goal" — that module's own
docstring), one-directional, and never crosses the Application Layer
boundary; `GoalDTO` is this layer's own read projection for
`GetGoalHandler`/`ListGoalsHandler`, a different consumer with different
reasons to change independently. See `docs/adr/0028-goal-application-
use-cases.md`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from app.domain.goal.enums import GoalStatus, GoalType
from app.domain.goal.identifiers import GoalId
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

if TYPE_CHECKING:
    # Import only for the type checker — see UserDTO's identical note
    # for why this avoids a real circular import at module load time.
    from app.domain.goal.goal import Goal


@dataclass(frozen=True, kw_only=True)
class GoalDTO:
    """An immutable, read-only snapshot of one `Goal`, taken at query
    time."""

    goal_id: GoalId
    user_id: UserId
    goal_type: GoalType
    name: GoalName
    target_date: TargetDate
    created_at: datetime
    description: GoalDescription | None
    target_weight: TargetWeight | None
    target_body_fat: TargetBodyFat | None
    target_strength: TargetStrength | None
    priority: Priority | None
    notes: GoalNotes
    status: GoalStatus
    updated_at: datetime | None
    completed_at: datetime | None
    cancelled_at: datetime | None

    @classmethod
    def from_goal(cls, goal: Goal) -> GoalDTO:
        """Builds a DTO from a live `Goal` aggregate. One-directional on
        purpose, mirroring `ReadinessDTO.from_readiness` — `Goal` never
        depends on this type.
        """
        return cls(
            goal_id=goal.id,
            user_id=goal.user_id,
            goal_type=goal.goal_type,
            name=goal.name,
            target_date=goal.target_date,
            created_at=goal.created_at,
            description=goal.description,
            target_weight=goal.target_weight,
            target_body_fat=goal.target_body_fat,
            target_strength=goal.target_strength,
            priority=goal.priority,
            notes=goal.notes,
            status=goal.status,
            updated_at=goal.updated_at,
            completed_at=goal.completed_at,
            cancelled_at=goal.cancelled_at,
        )
