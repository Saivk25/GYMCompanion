"""`UpdateWorkoutCommand`: the input to `UpdateWorkoutHandler`.

A full replacement of both `goal` and `notes`, the same
"caller-supplies-the-complete-new-value" shape
`app.application.user.commands.update_preferences.
UpdatePreferencesCommand` uses — `None` means "clear this field," not
"leave it unchanged." A caller that wants to change only one field
resupplies the other's current value; this keeps the command's own
shape simple and matches every other update command in this codebase,
rather than introducing a separate "unset" sentinel this phase's task
does not ask for.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.command import Command
from app.domain.user.identifiers import UserId
from app.domain.workout.identifiers import WorkoutId
from app.domain.workout.value_objects import WorkoutGoal, WorkoutNotes


@dataclass(frozen=True, kw_only=True)
class UpdateWorkoutCommand(Command):
    """Replace an existing Workout's goal and notes.

    `requester_id` is the authenticated caller — see
    `app.application.workout.queries.get_workout.GetWorkoutQuery`'s own
    module docstring for the full ownership-check reasoning, which
    applies identically here.
    """

    workout_id: WorkoutId
    requester_id: UserId
    goal: WorkoutGoal | None
    notes: WorkoutNotes | None
