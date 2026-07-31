"""`CompleteWorkoutSessionCommand`: the input to
`CompleteWorkoutSessionHandler`.

Carries exactly what `WorkoutSession.complete(...)` needs. See
`docs/adr/0024-workout-application-use-cases.md` for why this handler
also advances the parent `Workout` and invokes
`ProgressiveOverloadRuleEngine`/`TrainingLoadRuleEngine`.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.command import Command
from app.domain.workout_session.identifiers import WorkoutSessionId
from app.domain.workout_session.value_objects import (
    CompletionPercentage,
    SessionDuration,
    SessionRating,
)


@dataclass(frozen=True, kw_only=True)
class CompleteWorkoutSessionCommand(Command):
    """Mark an active WorkoutSession complete."""

    session_id: WorkoutSessionId
    duration: SessionDuration
    completion_percentage: CompletionPercentage
    rating: SessionRating | None = None
