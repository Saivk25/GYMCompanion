# ADR 0009: ExercisePerformance/ExerciseSet are entities/value objects owned by WorkoutSession, not a separate aggregate

- Status: accepted
- Date: 2026-07-29

## Context

Sprint 2, Step 5 asked for `ExercisePerformance` (an exercise's worth of
logged sets within a session: `ExerciseId`, ordered `ExerciseSet`s, notes)
and `ExerciseSet` (set number, weight, reps, RPE, completed flag), stated
explicitly as *not* a separate aggregate: "Treat ExercisePerformance and
ExerciseSet as entities/value objects owned by the WorkoutSession
aggregate. Do not introduce another repository." The task also included an
explicit recommendation to make `ExercisePerformance` an owned entity
rather than a standalone aggregate with its own repository, reasoning that
a session and what was performed in it are created, modified, and
persisted together, and that this shape will simplify future rule engines
(progressive overload, PR detection, analytics) that need to read a whole
session's performance data at once.

This matches the Domain Model & Decision Engine Bible's own structure
(Section 4.7, Table 10): "has many ExerciseSets" is listed as a
*relationship* of `WorkoutSession`, not a separate top-level entry in the
aggregate table (Table 2's bounded-context inventory lists `WorkoutSession`
and `ExerciseSet` together under Training, not as independently addressable
aggregates). Three concrete design questions still needed answers before
writing code, none fully specified by the task:

1. Does `ExercisePerformance` need its own identity, or can it be a value
   object like `ExerciseSet`?
2. Where does "cannot modify sets once WorkoutSession is Completed or
   Abandoned" get enforced, given neither child object has any way to see
   its owning session's status?
3. Are `weight`/`reps`/`rpe` required together with `set_number` at
   logging time, or does an `ExerciseSet` get built up field by field
   before being marked `completed`?

## Decision

1. **`ExercisePerformance` is an `Entity` (own identity via
   `ExercisePerformanceId`); `ExerciseSet` is a `ValueObject`.** A session
   can plausibly contain two performances of the same exercise (e.g. a
   primary lift, accessory work, then a return to the primary lift later
   in the session) that need to stay distinguishable even if their
   `exercise_id` and current sets happen to coincide — that needs
   identity. Within one `ExercisePerformance`, by contrast, "cannot
   duplicate set numbers" already makes `set_number` a natural unique key,
   so a second, synthetic identity for `ExerciseSet` would add machinery
   with nothing left for it to do; marking a set complete
   (`ExerciseSet.mark_completed()`) returns a new immutable instance that
   `ExercisePerformance` substitutes into its ordered tuple, the same
   "value object replaced wholesale on change" discipline every other
   value object in this codebase follows.

2. **No `ExercisePerformanceRepository` exists, and `WorkoutSessionRepository`
   gains no new methods.** `ExercisePerformance` and `ExerciseSet` are only
   ever reachable through a `WorkoutSession` — loaded, mutated, and saved
   as part of loading, mutating, and saving the session that owns them.
   This is a direct implementation of the task's own instruction and the
   user's recommendation, and is the standard DDD "aggregate boundary"
   pattern: one repository per consistency boundary, not one per entity.

3. **"Cannot modify sets once Completed/Abandoned" is enforced by
   `WorkoutSession`, not by `ExercisePerformance` or `ExerciseSet`.**
   Neither child object stores or can see the owning session's `_status`;
   every mutating `WorkoutSession` method that touches an
   `ExercisePerformance` (`add_exercise`, `remove_exercise`, `log_set`,
   `complete_set`, `update_exercise_notes`) calls a private
   `_ensure_mutable()` guard before delegating. This is the same "the
   aggregate root enforces what no single child can see" reasoning
   `app.domain.exercise.exercise`'s muscle-overlap cross-field check
   already established, applied one level down from "cross-field" to
   "cross-entity."

4. **`update_exercise_notes()` *is* blocked once Completed/Abandoned** —
   deliberately different from `WorkoutSession.update_notes()`, which ADR
   0008 exempted based on the Bible's "corrections are appended as a note,
   never an overwrite" allowance for session-level notes. That allowance
   is stated for the session's own notes; per-exercise performance data
   (sets and their notes) is exactly the historical record it protects,
   not a second place the same allowance also applies. Once a session
   closes, what was actually performed is final.

5. **`ExerciseSet.set_number`, `weight`, `reps`, and `rpe` are supplied
   together when a set is logged; `completed` defaults to `False` and is
   flipped separately by `ExercisePerformance.complete_set()`.** This
   models "record what just happened" as one action, with a distinct
   confirmation step — which is what the task's dedicated
   `ExerciseSetCompleted` event (as opposed to the catch-all
   `ExercisePerformanceUpdated`) implies exists for a reason. `RPE`
   required at logging time, not only at completion, is a modeling choice:
   this increment treats "log a set" as recording an already-finished set
   (matching "ExercisePerformance ... models what the user actually
   performed"), not a live rep-by-rep tracker.

## Consequences

Four Step-5 events exist, exactly as named: `ExerciseAddedToSession`,
`ExerciseRemovedFromSession`, `ExerciseSetCompleted`,
`ExercisePerformanceUpdated`. The last one is intentionally overloaded —
both "a new set was logged" and "notes were updated" raise it, since the
task names exactly four events and neither of those two actions is called
out with its own name. A future increment splitting these into more
specific events (e.g. `ExerciseSetLogged`) is additive, not breaking.

Any future domain service reading a whole session's performance (PR
detection, progressive overload, analytics, reports — all named in this
increment's own Goal, none built yet) reads it through
`WorkoutSession.exercise_performances` or the extended
`WorkoutSessionContext` (which now carries a tuple of
`ExercisePerformanceContext` snapshots, one per performance, each carrying
its own `ExerciseSet` tuple) — never through a separate repository query,
because none exists or should be added while these stay owned entities.

If a future requirement genuinely needs to query performances
independently of their session (e.g. "every time a user did this exercise,
across all sessions" — `ExerciseHistory`, Section 4's own denormalized read
model, built from events rather than a live query) that is a new read
model built from the events this aggregate already raises, not a reason to
promote `ExercisePerformance` to its own aggregate with its own
repository.
