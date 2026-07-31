"""`LogExerciseSetCommand`: the input to `LogExerciseSetHandler`.

Carries `exercise_id` as a typed reference, matching `WorkoutSession.
add_exercise(...)`'s own documented "typed reference only; no
repository lookup [implied]" contract — this command's own handler is
what performs the actual `ExerciseRepository` lookup (see
`log_exercise_set_handler.py`), the same "reference in, existence
checked by the caller" division of responsibility the domain layer
already establishes. No `performance_id` field: this handler finds an
existing `ExercisePerformance` for `exercise_id` within the session, or
creates one, so a caller never needs to know whether this is the first
set logged for this exercise in this session.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.command import Command
from app.domain.exercise.identifiers import ExerciseId
from app.domain.workout_session.exercise_set import SetNumber, SetReps, SetRPE, SetWeight
from app.domain.workout_session.identifiers import WorkoutSessionId


@dataclass(frozen=True, kw_only=True)
class LogExerciseSetCommand(Command):
    """Log one set of one exercise within an active WorkoutSession."""

    session_id: WorkoutSessionId
    exercise_id: ExerciseId
    set_number: SetNumber
    weight: SetWeight
    reps: SetReps
    rpe: SetRPE
