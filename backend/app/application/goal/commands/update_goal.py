"""`UpdateGoalCommand`: the input to `UpdateGoalHandler`.

One command for `Goal.update(...)`'s full field set — `name`,
`description`, `target_date`, `target_weight`, `target_body_fat`,
`target_strength`, `priority`, `notes` — matching `Goal.update()` being
a single aggregate method covering every mutable field at once (unlike
`Readiness`, which exposes three narrower `update_*()` methods and so
gets three narrower commands). This mirrors
`app.application.workout.commands.update_workout.UpdateWorkoutCommand`'s
own "one command per aggregate method, not per field" shape. Every field
but `goal_id` is optional: `None` means "leave unchanged," the same
convention `Goal.update()` itself documents — not "clear it."
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.command import Command
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


@dataclass(frozen=True, kw_only=True)
class UpdateGoalCommand(Command):
    """Replace whichever fields are given on an existing, Active Goal."""

    goal_id: GoalId
    name: GoalName | None = None
    description: GoalDescription | None = None
    target_date: TargetDate | None = None
    target_weight: TargetWeight | None = None
    target_body_fat: TargetBodyFat | None = None
    target_strength: TargetStrength | None = None
    priority: Priority | None = None
    notes: GoalNotes | None = None
