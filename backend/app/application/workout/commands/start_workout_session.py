"""`StartWorkoutSessionCommand`: the input to
`StartWorkoutSessionHandler`.

`user_id` is deliberately absent — `StartWorkoutSessionHandler` derives
it from the `Workout` it loads (`workout.user_id`), rather than trusting
a second, independently-supplied value that could disagree with the
Workout's own owner. See
`docs/adr/0024-workout-application-use-cases.md` for why this handler
orchestrates both `Workout` and `WorkoutSession`.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.command import Command
from app.domain.workout.identifiers import WorkoutId
from app.domain.workout_session.value_objects import SessionDate


@dataclass(frozen=True, kw_only=True)
class StartWorkoutSessionCommand(Command):
    """Start a new WorkoutSession executing an existing Workout."""

    workout_id: WorkoutId
    session_date: SessionDate
