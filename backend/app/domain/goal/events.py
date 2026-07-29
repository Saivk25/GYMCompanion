"""Domain events raised by the Goal aggregate.

Scoped to exactly the four events this increment's task named —
`GoalCreated`, `GoalUpdated`, `GoalCompleted`, `GoalCancelled` — the same
"raise only what the aggregate's own methods actually do" discipline every
other aggregate's `events.py` already follows.

Notably absent: a `GoalExpired` event. `GoalStatus.EXPIRED` is a legal
status value (`enums.py`), but `Goal` provides no method that transitions
into it — see `docs/adr/0012-goal-lifecycle-and-expired-with-no-transition.md`
for why. `GoalUpdated` carries only `name` (like
`app.domain.exercise.events.ExerciseUpdated`), not every field `update()`
can change — see that event's docstring for the same reasoning applied
here: `Goal.update()` covers many fields, but the event only needs to
carry what a first subscriber would use to identify which goal changed
without a full snapshot.
"""

from dataclasses import dataclass

from app.domain.goal.enums import GoalType
from app.domain.goal.identifiers import GoalId
from app.domain.goal.value_objects import GoalName, TargetDate
from app.domain.shared_kernel.events import DomainEvent
from app.domain.user.identifiers import UserId


@dataclass(frozen=True, kw_only=True)
class GoalCreated(DomainEvent):
    """A new Goal was created via `Goal.create(...)`. Carries `goal_type`,
    `name`, and `target_date` — the fields most documented downstream
    readers (Plan generation, NutritionPattern guidance — neither built
    yet) would need first, the same "carry what a first subscriber needs"
    choice `app.domain.workout.events.WorkoutPlanned` makes.
    """

    goal_id: GoalId
    user_id: UserId
    goal_type: GoalType
    name: GoalName
    target_date: TargetDate


@dataclass(frozen=True, kw_only=True)
class GoalUpdated(DomainEvent):
    """`Goal.update(...)` changed one or more fields. Carries `name`, the
    same choice `app.domain.exercise.events.ExerciseUpdated` makes for its
    own multi-field `update()`.
    """

    goal_id: GoalId
    name: GoalName


@dataclass(frozen=True, kw_only=True)
class GoalCompleted(DomainEvent):
    """`Goal.complete(...)` moved the goal to Completed."""

    goal_id: GoalId
    user_id: UserId


@dataclass(frozen=True, kw_only=True)
class GoalCancelled(DomainEvent):
    """`Goal.cancel(...)` moved the goal to Cancelled."""

    goal_id: GoalId
    user_id: UserId
