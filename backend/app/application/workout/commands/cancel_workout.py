"""`CancelWorkoutCommand`: the input to `CancelWorkoutHandler`.

Cancels only the `Workout` itself — deliberately does not cascade to
any `WorkoutSession` executing it. See
`docs/adr/0024-workout-application-use-cases.md` for why.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.command import Command
from app.domain.workout.identifiers import WorkoutId


@dataclass(frozen=True, kw_only=True)
class CancelWorkoutCommand(Command):
    """Cancel an existing, not-yet-terminal Workout."""

    workout_id: WorkoutId
