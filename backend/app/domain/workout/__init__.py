"""The Workout aggregate: Sprint 2's second real aggregate, built on the
Sprint 1 shared kernel (`app.domain.shared_kernel`) and following the same
pattern as `app.domain.user`. Training bounded context (Domain Model &
Decision Engine Bible, Section 3, Table 2), closest deep dive in Section
4.7 (`WorkoutSession`).

Scope of this first increment — deliberately smaller than the Bible's full
Training bounded context, not an oversight: `WorkoutTemplate`, `WorkoutPlan`
(+ `PlanVersion`), and `ExerciseSet` (Sections 4.5, 4.6, 4.7) are not
modeled yet. This increment's `Workout` is a standalone aggregate — planned,
started, completed, or cancelled directly, with no owning Plan and no
logged sets. See `docs/adr/0006-workout-aggregate-first-increment.md` for
the full reasoning and what a future increment needs to reconcile.

Depends on nothing outside the Python standard library,
`app.domain.shared_kernel`, and `app.domain.user` (for the `UserId` a
Workout belongs to — aggregates reference each other by id only, never by
object reference) — enforced by the same statically-checked rule as the
rest of `app/domain` (`tests/domain/test_import_boundaries.py`).
"""

from app.domain.workout.context import WorkoutContext
from app.domain.workout.enums import WorkoutStatus
from app.domain.workout.events import (
    WorkoutCancelled,
    WorkoutCompleted,
    WorkoutPlanned,
    WorkoutStarted,
)
from app.domain.workout.identifiers import WorkoutId
from app.domain.workout.repository import WorkoutRepository
from app.domain.workout.value_objects import (
    WorkoutDate,
    WorkoutDuration,
    WorkoutGoal,
    WorkoutName,
    WorkoutNotes,
)
from app.domain.workout.workout import Workout

__all__ = [
    "Workout",
    "WorkoutCancelled",
    "WorkoutCompleted",
    "WorkoutContext",
    "WorkoutDate",
    "WorkoutDuration",
    "WorkoutGoal",
    "WorkoutId",
    "WorkoutName",
    "WorkoutNotes",
    "WorkoutPlanned",
    "WorkoutRepository",
    "WorkoutStarted",
    "WorkoutStatus",
]
