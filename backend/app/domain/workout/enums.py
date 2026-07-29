"""Closed-set categorical values used by the Workout aggregate.

See `docs/adr/0006-workout-aggregate-first-increment.md` for why
`WorkoutStatus` uses this specific four-state shape rather than the Domain
Model & Decision Engine Bible's five-state `WorkoutSession` lifecycle
(Section 7.1, Table 30: Scheduled -> InProgress -> Completed / Skipped ->
Reviewed).
"""

from enum import Enum


class WorkoutStatus(str, Enum):
    """The Workout aggregate's lifecycle: Planned -> InProgress ->
    Completed, with Cancelled reachable from either Planned or InProgress.
    Legal transitions are enforced by `Workout`'s own transition table
    (`workout.py`), not by this enum; this type only names the possible
    values.
    """

    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
