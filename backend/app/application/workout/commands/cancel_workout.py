"""`CancelWorkoutCommand`: the input to `CancelWorkoutHandler`.

Cancels only the `Workout` itself — deliberately does not cascade to
any `WorkoutSession` executing it. See
`docs/adr/0024-workout-application-use-cases.md` for why.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.command import Command
from app.domain.user.identifiers import UserId
from app.domain.workout.identifiers import WorkoutId


@dataclass(frozen=True, kw_only=True)
class CancelWorkoutCommand(Command):
    """Cancel an existing, not-yet-terminal Workout.

    `requester_id` is the authenticated caller — see
    `app.application.workout.queries.get_workout.GetWorkoutQuery`'s own
    module docstring for the full ownership-check reasoning, which
    applies identically here.
    """

    workout_id: WorkoutId
    requester_id: UserId
