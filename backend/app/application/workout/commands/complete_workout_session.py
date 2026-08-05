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
from app.domain.user.identifiers import UserId
from app.domain.workout_session.identifiers import WorkoutSessionId
from app.domain.workout_session.value_objects import (
    CompletionPercentage,
    SessionDuration,
    SessionRating,
)


@dataclass(frozen=True, kw_only=True)
class CompleteWorkoutSessionCommand(Command):
    """Mark an active WorkoutSession complete.

    `requester_id` is the authenticated caller — see
    `app.application.workout.queries.get_workout_session.
    GetWorkoutSessionQuery`'s own module docstring for the full
    ownership-check reasoning, which applies identically here.
    """

    session_id: WorkoutSessionId
    requester_id: UserId
    duration: SessionDuration
    completion_percentage: CompletionPercentage
    rating: SessionRating | None = None
