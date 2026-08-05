"""`StartWorkoutSessionCommand`: the input to
`StartWorkoutSessionHandler`.

The `Workout`'s own `user_id` is deliberately not duplicated onto the
new `WorkoutSession` from a client-supplied value — `StartWorkoutSessionHandler`
derives it from the `Workout` it loads (`workout.user_id`), rather than
trusting a second, independently-supplied value that could disagree
with the Workout's own owner. See
`docs/adr/0024-workout-application-use-cases.md` for why this handler
orchestrates both `Workout` and `WorkoutSession`.

`requester_id` (the authenticated caller) *is* carried here, distinct
from that reasoning: it is not the new session's owner (that is always
`workout.user_id`, unconditionally), it is who is asking to start one.
`StartWorkoutSessionHandler` compares it against the loaded `Workout`'s
own `user_id` — the only aggregate that exists at the point this check
must run, since no `WorkoutSession` exists yet — via
`app.application.shared.ownership.ensure_owner`. See
`docs/adr/0033-resource-ownership-authorization.md`.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.command import Command
from app.domain.user.identifiers import UserId
from app.domain.workout.identifiers import WorkoutId
from app.domain.workout_session.value_objects import SessionDate


@dataclass(frozen=True, kw_only=True)
class StartWorkoutSessionCommand(Command):
    """Start a new WorkoutSession executing an existing Workout."""

    workout_id: WorkoutId
    requester_id: UserId
    session_date: SessionDate
