"""The Goal aggregate root.

The canonical representation of a user's fitness objectives. Domain Model
& Decision Engine Bible, Section 4.4's `Goal` ("holds goal type(s),
priority order, target timeline, success-evidence definition", Table 6) is
the closest analog. This increment stores goals only — it does not
calculate plans, recommendations, readiness, or analytics from them; those
read this aggregate's events, never the other way around (the same
relationship every other Sprint 2 aggregate's module docstring describes
between itself and its future consumers).

`GoalStatus` (four states: `Active`/`Completed`/`Cancelled`/`Expired`) is
deliberately smaller than the Bible's own six-state `Goal` lifecycle
(`Proposed -> Active -> Achieved / Abandoned / Superseded -> Archived`,
Section 7.4), and this increment implements no priority-ranking conflict
resolution across a user's concurrent goals ("Multiple Active goals
require an explicit ranking", "Two Active Goals conflict in the same
phase | Surfaced to the user as an explicit choice" — both Section 7.4).
See `docs/adr/0012-goal-lifecycle-and-expired-with-no-transition.md` for
the full reasoning, including why `GoalStatus.EXPIRED` exists as a value
here but no method on this class transitions into it.

Tenant-scoped like every other per-user aggregate in this codebase
(carries `user_id`). Every `Goal` is created directly `Active` — there is
no `Proposed` state requiring a separate activation step, the same
"immediately usable" simplification `app.domain.exercise.exercise.
Exercise.create()` already makes for its own, smaller lifecycle.
"""

from __future__ import annotations

from datetime import datetime

from app.domain.goal.enums import GoalStatus, GoalType
from app.domain.goal.events import GoalCancelled, GoalCompleted, GoalCreated, GoalUpdated
from app.domain.goal.identifiers import GoalId
from app.domain.goal.value_objects import (
    GoalDescription,
    GoalName,
    GoalNotes,
    Priority,
    TargetBodyFat,
    TargetDate,
    TargetStrength,
    TargetWeight,
)
from app.domain.shared_kernel.aggregate_root import AggregateRoot
from app.domain.shared_kernel.clock import Clock
from app.domain.shared_kernel.validation import ensure
from app.domain.user.identifiers import UserId

# Same table-driven technique as every other aggregate's status machine in
# this codebase: every terminal state maps to an empty allowed set, which
# is what makes "cannot complete twice" and "cannot cancel after
# completion" true by construction rather than a separate guard clause.
# `EXPIRED` is included (mapped to an empty set, same as the other two
# terminal states) purely so `_transition_to`/`_ensure_mutable` never
# KeyError against a rehydrated Goal that already has this status — no
# code path in this class ever sets a Goal's status to `EXPIRED` itself;
# see the module docstring and ADR 0012 for why.
_ALLOWED_TRANSITIONS: dict[GoalStatus, frozenset[GoalStatus]] = {
    GoalStatus.ACTIVE: frozenset({GoalStatus.COMPLETED, GoalStatus.CANCELLED}),
    GoalStatus.COMPLETED: frozenset(),
    GoalStatus.CANCELLED: frozenset(),
    GoalStatus.EXPIRED: frozenset(),
}


class Goal(AggregateRoot[GoalId]):
    """The Goal aggregate. See the module docstring for scope and the ADR
    for the lifecycle/`EXPIRED` reasoning.

    Construct a brand-new goal via the `create()` factory, never
    `Goal(...)` directly — the constructor is also used to rehydrate an
    existing goal from a repository, where re-raising `GoalCreated` would
    be wrong.
    """

    def __init__(
        self,
        goal_id: GoalId,
        *,
        user_id: UserId,
        goal_type: GoalType,
        name: GoalName,
        target_date: TargetDate,
        created_at: datetime,
        description: GoalDescription | None = None,
        target_weight: TargetWeight | None = None,
        target_body_fat: TargetBodyFat | None = None,
        target_strength: TargetStrength | None = None,
        priority: Priority | None = None,
        notes: GoalNotes | None = None,
        status: GoalStatus = GoalStatus.ACTIVE,
        updated_at: datetime | None = None,
        completed_at: datetime | None = None,
        cancelled_at: datetime | None = None,
    ) -> None:
        super().__init__(goal_id)
        ensure(created_at.tzinfo is not None, "created_at must be timezone-aware")
        self._user_id = user_id
        self._goal_type = goal_type
        self._name = name
        self._target_date = target_date
        self._created_at = created_at
        self._description = description
        self._target_weight = target_weight
        self._target_body_fat = target_body_fat
        self._target_strength = target_strength
        self._priority = priority
        self._notes = notes if notes is not None else GoalNotes()
        self._status = status
        self._updated_at = updated_at
        self._completed_at = completed_at
        self._cancelled_at = cancelled_at

    @classmethod
    def create(
        cls,
        *,
        goal_id: GoalId,
        user_id: UserId,
        goal_type: GoalType,
        name: GoalName,
        target_date: TargetDate,
        clock: Clock,
        description: GoalDescription | None = None,
        target_weight: TargetWeight | None = None,
        target_body_fat: TargetBodyFat | None = None,
        target_strength: TargetStrength | None = None,
        priority: Priority | None = None,
        notes: GoalNotes | None = None,
    ) -> Goal:
        """Creates a brand-new Goal in the Active state and records
        `GoalCreated`. `goal_id` is generated by the caller
        (`GoalId.generate()`) before calling this — the same convention
        every other aggregate's factory follows.
        """
        created_at = clock.now()
        goal = cls(
            goal_id,
            user_id=user_id,
            goal_type=goal_type,
            name=name,
            target_date=target_date,
            created_at=created_at,
            description=description,
            target_weight=target_weight,
            target_body_fat=target_body_fat,
            target_strength=target_strength,
            priority=priority,
            notes=notes,
        )
        goal.record_event(
            GoalCreated(
                occurred_at=created_at,
                goal_id=goal_id,
                user_id=user_id,
                goal_type=goal_type,
                name=name,
                target_date=target_date,
            )
        )
        return goal

    @property
    def user_id(self) -> UserId:
        return self._user_id

    @property
    def goal_type(self) -> GoalType:
        return self._goal_type

    @property
    def name(self) -> GoalName:
        return self._name

    @property
    def target_date(self) -> TargetDate:
        return self._target_date

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def description(self) -> GoalDescription | None:
        return self._description

    @property
    def target_weight(self) -> TargetWeight | None:
        return self._target_weight

    @property
    def target_body_fat(self) -> TargetBodyFat | None:
        return self._target_body_fat

    @property
    def target_strength(self) -> TargetStrength | None:
        return self._target_strength

    @property
    def priority(self) -> Priority | None:
        return self._priority

    @property
    def notes(self) -> GoalNotes:
        return self._notes

    @property
    def status(self) -> GoalStatus:
        return self._status

    @property
    def updated_at(self) -> datetime | None:
        return self._updated_at

    @property
    def completed_at(self) -> datetime | None:
        return self._completed_at

    @property
    def cancelled_at(self) -> datetime | None:
        return self._cancelled_at

    def update(
        self,
        *,
        clock: Clock,
        name: GoalName | None = None,
        description: GoalDescription | None = None,
        target_date: TargetDate | None = None,
        target_weight: TargetWeight | None = None,
        target_body_fat: TargetBodyFat | None = None,
        target_strength: TargetStrength | None = None,
        priority: Priority | None = None,
        notes: GoalNotes | None = None,
    ) -> None:
        """Replaces whichever fields are given (`None` means "leave
        unchanged", not "clear it" — pass an empty value object explicitly
        to clear one where that's legal), and records one `GoalUpdated`
        event. Blocked once Completed, Cancelled, or Expired: "Cannot
        update completed goals" / "Cannot update cancelled goals" — the
        task's Rules name those two specifically, and this method extends
        the same immutability to Expired for consistency (see the class
        docstring and ADR 0012).
        """
        self._ensure_mutable()
        if name is not None:
            self._name = name
        if description is not None:
            self._description = description
        if target_date is not None:
            self._target_date = target_date
        if target_weight is not None:
            self._target_weight = target_weight
        if target_body_fat is not None:
            self._target_body_fat = target_body_fat
        if target_strength is not None:
            self._target_strength = target_strength
        if priority is not None:
            self._priority = priority
        if notes is not None:
            self._notes = notes

        self._updated_at = clock.now()
        self.record_event(
            GoalUpdated(
                occurred_at=self._updated_at,
                goal_id=self.id,
                name=self._name,
            )
        )

    def complete(self, *, clock: Clock) -> None:
        """Active -> Completed. "Cannot complete twice" is true by
        construction: `Completed` maps to an empty allowed-transitions
        set."""
        self._transition_to(GoalStatus.COMPLETED)
        self._completed_at = clock.now()
        self.record_event(
            GoalCompleted(occurred_at=self._completed_at, goal_id=self.id, user_id=self._user_id)
        )

    def cancel(self, *, clock: Clock) -> None:
        """Active -> Cancelled. "Cannot cancel after completion" is true
        by construction: `Completed` maps to an empty allowed-transitions
        set, so `Completed -> Cancelled` is never in it."""
        self._transition_to(GoalStatus.CANCELLED)
        self._cancelled_at = clock.now()
        self.record_event(
            GoalCancelled(occurred_at=self._cancelled_at, goal_id=self.id, user_id=self._user_id)
        )

    def _ensure_mutable(self) -> None:
        ensure(
            self._status is GoalStatus.ACTIVE,
            f"cannot update a goal in status {self._status.value!r}",
        )

    def _transition_to(self, target: GoalStatus) -> None:
        allowed = _ALLOWED_TRANSITIONS[self._status]
        ensure(
            target in allowed,
            f"cannot transition goal status from {self._status.value!r} to {target.value!r}",
        )
        self._status = target
