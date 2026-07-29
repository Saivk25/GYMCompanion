"""Closed-set categorical values used by the WorkoutSession aggregate."""

from enum import Enum


class SessionStatus(str, Enum):
    """The WorkoutSession aggregate's lifecycle: Planned -> Active ->
    Completed, with Abandoned reachable from either Planned or Active.
    Deliberately named differently from `app.domain.workout.enums.
    WorkoutStatus` ("Active" here, "InProgress" there; "Abandoned" here,
    "Cancelled" there) even though the shapes are similar — see
    `docs/adr/0008-workout-session-execution-record.md` for why these are
    two distinct concepts (a planned intention vs. its execution record),
    not the same status type reused twice. Legal transitions are enforced
    by `WorkoutSession`'s own transition table (`workout_session.py`), not
    by this enum.
    """

    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
