"""Closed-set categorical values used by the Goal aggregate.

`GoalType` and `GoalStatus` inherit `str` as well as `Enum` so a member
serializes to exactly its `.value` wherever it's written to JSON, a
database column, or an event payload — the same convention every other
enum in this codebase follows.
"""

from enum import Enum


class GoalType(str, Enum):
    """What kind of objective this Goal represents. The Domain Model &
    Decision Engine Bible names `goal_type` as a key attribute (Section
    4.4, Table 6) without enumerating a fixed set of values; this
    increment's six members are this task's own closed list, covering the
    Product Bible's named goal categories.
    """

    LOSE_FAT = "lose_fat"
    GAIN_MUSCLE = "gain_muscle"
    MAINTAIN = "maintain"
    STRENGTH = "strength"
    ENDURANCE = "endurance"
    GENERAL_HEALTH = "general_health"


class GoalStatus(str, Enum):
    """The Goal aggregate's lifecycle. Deliberately smaller than the
    Bible's own `Goal` state machine (Section 7.4: `Proposed -> Active ->
    Achieved / Abandoned / Superseded -> Archived`) — see
    `docs/adr/0012-goal-lifecycle-and-expired-with-no-transition.md` for
    the full reasoning, including why `EXPIRED` exists as a value here but
    `Goal` provides no method that transitions into it.

    Legal transitions are enforced by `Goal`'s own transition table
    (`goal.py`), not by this enum.
    """

    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
