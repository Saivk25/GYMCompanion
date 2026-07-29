# ADR 0012: Goal's lifecycle is a 4-state simplification of the Bible's model, and EXPIRED is a legal value with no domain-triggered transition

- Status: accepted
- Date: 2026-07-30

## Context

Sprint 2, Step 9 asked for a `Goal` aggregate: "the canonical
representation of a user's fitness objectives," with an explicit
`GoalStatus` enum (`Active`/`Completed`/`Cancelled`/`Expired`), a `GoalType`
enum, eight value objects, and four events
(`GoalCreated`/`GoalUpdated`/`GoalCompleted`/`GoalCancelled` — no
`GoalExpired`). The Rules list states "Cannot complete twice," "Cannot
cancel after completion," "Cannot update completed goals," and "Cannot
update cancelled goals," but says nothing about `Expired` beyond its
presence as a status value.

The Domain Model & Decision Engine Bible's own `Goal` (Section 4.4, Table
6) carries a richer, six-state lifecycle (Section 7.4:
`Proposed -> Active -> Achieved / Abandoned / Superseded -> Archived`) and
also names explicit priority-ranking rules for concurrent goals ("Multiple
Active goals require an explicit ranking," "Two Active Goals conflict in
the same phase | Surfaced to the user as an explicit choice"). Three things
needed a decision before writing code, following the pattern ADR
0006/0008/0009/0010/0011 already established of naming an ambiguity
explicitly rather than picking a reading silently:

1. **Lifecycle size.** The task's own `GoalStatus` (four states) is
   smaller than the Bible's own six-state model, and has no `Proposed`
   pre-activation state — should `Goal.create()` require a separate
   activation step, or start directly `Active`?

2. **`EXPIRED` with no matching event.** `GoalStatus.EXPIRED` is named as a
   status value, but the task's event list has no `GoalExpired`. Every
   other status transition on every other aggregate in this codebase
   pairs one transition method with one event
   (`Exercise.deprecate()` -> `ExerciseDeprecated`,
   `Goal.complete()` -> `GoalCompleted`, `Goal.cancel()` ->
   `GoalCancelled`). No such pairing is named for `Expired`.

3. **Concurrent-goal ranking.** The Bible's "Multiple Active goals require
   an explicit ranking" and conflict-surfacing rules describe behavior
   across a *user's* goals, not any single `Goal`'s own invariants — no
   such cross-aggregate check is named in this task's Rules list, and
   `GoalRepository` (matching every other aggregate's repository this
   sprint) declares no query method that could support one.

4. **`update()`'s block list vs. `Expired`.** The Rules list names
   `update()` as blocked only for Completed and Cancelled — should the
   same method also block on `Expired`, an unnamed case?

## Decision

1. **`Goal.create()` starts every goal directly `Active`.** The same
   "immediately usable, no separate activation step" simplification
   `Exercise.create()` already makes for its own, smaller lifecycle (see
   `Exercise`'s module docstring) — nothing in this task's Rules names a
   `Proposed` state or an activation method, so none is added.

2. **`GoalStatus.EXPIRED` is included in `_ALLOWED_TRANSITIONS` (mapped to
   an empty set, like the other two terminal states), but no method on
   `Goal` ever sets a goal's status to `Expired`.** It exists purely so a
   `Goal` rehydrated from storage already in that status doesn't `KeyError`
   against the transition table. Reaching `Expired` at all — presumably by
   comparing `target_date` against the current date — is future,
   scheduler- or read-model-driven work with no domain method to trigger
   it in this increment, the same "raise only what's named" discipline
   applied since ADR 0005/0006/0008: since no `GoalExpired` event was
   named, no code path invents one.

3. **No priority-ranking or conflict-resolution logic across a user's
   concurrent goals is implemented.** `Priority` (this aggregate's own
   value object, see its docstring) validates one goal's own rank is
   within bounds; it enforces no uniqueness or ordering against a user's
   other goals. `GoalRepository` declares no "find all Active goals for a
   user" query, matching this sprint's precedent of not adding
   speculative query methods ahead of a concrete caller.

4. **`update()` is blocked whenever `status is not GoalStatus.ACTIVE`** —
   which includes `Expired`, not just the two states the Rules list names
   explicitly. This is the more consistent default absent any
   countervailing signal: every other terminal state in this codebase
   blocks mutation, and nothing in the task's text carves out an exception
   for `Expired` the way, for instance, `WorkoutSession.update_notes()`'s
   exception is backed by an explicit Bible quote. `_ensure_mutable()`
   checks equality to `ACTIVE` directly rather than listing the blocked
   states, so this also holds automatically for any future terminal state
   added to `GoalStatus` without a corresponding code change.

## Consequences

A future rule engine or scheduled job that marks goals `Expired` (e.g.,
"target_date has passed and status is still Active") will need to add its
own transition method and `GoalExpired` event to `Goal` — this increment
provides no hook for it beyond the enum member itself and the empty
transition-table entry that lets it round-trip through a repository
without error.

Any future work implementing the Bible's richer six-state lifecycle
(`Proposed`, `Achieved`, `Superseded`, `Archived`) or its concurrent-goal
ranking rules is a genuine extension of this aggregate, not a bug fix —
`GoalStatus` and `_ALLOWED_TRANSITIONS` will both need new entries, and
`GoalRepository` will need a query method it deliberately doesn't have
today.

Because `update()` blocks on any non-`Active` status rather than an
explicit list, adding a new terminal `GoalStatus` member later
automatically inherits the same mutation guard without a corresponding
change to `_ensure_mutable()` — only `_ALLOWED_TRANSITIONS` needs updating
to wire in how a goal reaches that new state.
