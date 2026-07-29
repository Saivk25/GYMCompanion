"""`GoalContext`: a read-only snapshot of a Goal for domain services.

Same purpose as every other `*Context` in this codebase: lets a future
domain service — Plan generation, NutritionPattern guidance, neither built
yet — consume everything it needs to know about one goal in a single
immutable value.
"""

from __future__ import annotations

from dataclasses import dataclass
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
from app.domain.shared_kernel.value_object import ValueObject
from app.domain.user.identifiers import UserId

if TYPE_CHECKING:
    # Import only for the type checker — see UserContext's identical note
    # for why this avoids a real circular import at module load time.
    from app.domain.goal.goal import Goal


@dataclass(frozen=True, kw_only=True)
class GoalContext(ValueObject):
    """An immutable snapshot of one Goal, taken at a point in time."""

    goal_id: GoalId
    user_id: UserId
    goal_type: GoalType
    name: GoalName
    target_date: TargetDate
    status: GoalStatus
    description: GoalDescription | None
    target_weight: TargetWeight | None
    target_body_fat: TargetBodyFat | None
    target_strength: TargetStrength | None
    priority: Priority | None
    notes: GoalNotes

    @classmethod
    def from_goal(cls, goal: Goal) -> GoalContext:
        """Builds a snapshot from a live `Goal` aggregate. One-directional
        on purpose: `Goal` does not know this type exists.
        """
        return cls(
            goal_id=goal.id,
            user_id=goal.user_id,
            goal_type=goal.goal_type,
            name=goal.name,
            target_date=goal.target_date,
            status=goal.status,
            description=goal.description,
            target_weight=goal.target_weight,
            target_body_fat=goal.target_body_fat,
            target_strength=goal.target_strength,
            priority=goal.priority,
            notes=goal.notes,
        )
