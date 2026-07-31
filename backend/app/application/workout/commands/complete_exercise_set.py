"""`CompleteExerciseSetCommand`: the input to
`CompleteExerciseSetHandler`.

`set_number` is a plain `int`, not `SetNumber` — matching `WorkoutSession.
complete_set(performance_id, set_number: int, ...)`'s own signature
exactly (`app.domain.workout_session.workout_session`); this command
carries the identical shape its handler forwards untouched.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.command import Command
from app.domain.workout_session.identifiers import ExercisePerformanceId, WorkoutSessionId


@dataclass(frozen=True, kw_only=True)
class CompleteExerciseSetCommand(Command):
    """Mark one previously logged set complete."""

    session_id: WorkoutSessionId
    performance_id: ExercisePerformanceId
    set_number: int
