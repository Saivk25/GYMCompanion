# ADR 0008: WorkoutSession — the execution record, split from Workout the plan

- Status: accepted
- Date: 2026-07-29

## Context

Sprint 2, Step 4 asked for a standalone `WorkoutSession` aggregate framed
explicitly against the aggregate built in Step 2: "Workout represents the
planned workout. Workout Session represents what actually happened." A
four-state lifecycle (`PLANNED`, `ACTIVE`, `COMPLETED`, `ABANDONED`), four
named events starting from `WorkoutSessionStarted` (no creation event),
five value objects, and eight explicit rules, with `ExerciseSet`,
`LoggedExercise`, progressive overload, and rest timers explicitly excluded.

ADR 0006 already flagged this exact split as open, deferred work: "most
plausibly, `Workout` becomes (or is absorbed into) `WorkoutSession` once a
`WorkoutPlan` aggregate exists to generate it from." This step answers part
of that question — not by merging `Workout` into `WorkoutSession`, but by
introducing `WorkoutSession` as its own aggregate, referencing `Workout` by
id, matching the Domain Model & Decision Engine Bible's own separation
(Section 4.6 `WorkoutPlan`/Section 4.7 `WorkoutSession`, Table 10) between a
plan and its execution record, without yet building the `WorkoutPlan` layer
above either.

Three decisions in this step depart from the pattern every prior aggregate
(`User`, `Workout`, `Exercise`) established, and needed to be made
deliberately rather than by silently copying precedent:

1. The task's own event list starts at `WorkoutSessionStarted` — there is
   no `WorkoutSessionPlanned`/`WorkoutSessionCreated` event, unlike
   `UserRegistered`, `WorkoutPlanned`, and `ExerciseCreated`, which all fire
   from their aggregate's factory method.
2. The task's rule "Duration must be positive" reads differently from
   `WorkoutDuration`'s existing "must not be negative" (Step 2), which
   permits zero.
3. The Bible's Table 10 "Versioning" row states, for the real
   `WorkoutSession`: "Immutable once Completed; corrections are appended as
   a note, never an overwrite" — the opposite of what `Workout.update_notes`
   and `Exercise.update` do (both reject edits once their aggregate reaches
   a terminal status).

## Decision

1. **`WorkoutSession.plan()` raises no domain event.** This is a literal,
   deliberate reading of the task's event list, not an oversight — the
   first event in the aggregate's life is `WorkoutSessionStarted`. No
   downstream capability named in the task's own "future systems" list
   (workout history, analytics, PR detection, progressive overload,
   recovery, AI coaching, reports) needs to react to a session merely being
   scheduled; every one of them cares about what happened during or after
   execution. If a future increment needs to notify on scheduling, the same
   "add an event only once a real subscriber needs it" discipline from ADR
   0005/0006 applies — add it then.

2. **`SessionDuration` requires a strictly positive `timedelta` (`> timedelta(0)`),
   not `>= timedelta(0)` like `WorkoutDuration`.** `WorkoutDuration` is a
   planning estimate that can legitimately be zero (an unstarted plan
   stub); `SessionDuration` only ever appears on a session that has
   actually run (`complete()`) or been partially run (`abandon()`) — a
   zero-length execution record has no meaning and most plausibly indicates
   a caller bug, so it is rejected at construction rather than allowed
   through and caught later by an analytics job.

3. **`SessionRating` is bounded 1–10.** Neither Bible pins an exact numeric
   range for the "RPE" field Table 10 names; 1–10 is this increment's own
   choice, matching the industry-standard RPE/Borg CR10 scale referenced
   elsewhere in the Bible's recovery and progressive-overload sections. A
   future increment reconciling with a specific RPE methodology may need to
   adjust these bounds; nothing about the aggregate's shape depends on the
   exact numbers.

4. **`WorkoutSession.update_notes()` is not blocked by `SessionStatus`,
   including after `Completed` or `Abandoned`** — a deliberate divergence
   from `Workout.update_notes`/`Exercise.update`, both of which reject edits
   once terminal. This follows the Bible's own stated rule for this
   aggregate specifically ("corrections are appended as a note, never an
   overwrite"), read as license to keep `update_notes` callable at any
   status. What is **not** implemented here is true append-only history —
   today's `update_notes` still replaces `SessionNotes` wholesale, the same
   as every other aggregate's update methods. A future increment
   implementing the Bible's literal "append, never overwrite" semantics
   (e.g. a list of timestamped note entries) is real, additional work, not
   assumed to already exist.

5. **`WorkoutSession` carries both `workout_id: WorkoutId` and
   `user_id: UserId`, both required.** `workout_id` was explicit in the
   Goal's framing (a session executes a specific planned workout);
   `user_id` was not named as a field in the task's "Implement" section but
   is inferred the same way ADR 0006 inferred it for `Workout` — every
   per-user execution record in this codebase is tenant-scoped, and a
   `WorkoutSession` without its own `user_id` would require an extra join
   through `Workout` for every tenant-scoping check, which the established
   `tenant_scope` convention (`app/infra/database.py`) does not do for any
   other aggregate.

## Consequences

`WorkoutSession` now references `Workout` by id only (`workout_id`), never
by object reference — the same cross-aggregate convention every prior step
has used and documented. No change to `Workout` was needed or made in this
step.

ADR 0006's deferred question — how `Workout` reconciles with the Bible's
`WorkoutTemplate -> WorkoutPlan -> WorkoutSession` hierarchy — is now
partially answered: this codebase's `Workout` most closely maps to a
`WorkoutPlan` (or a plan-less, directly-authored equivalent), and
`WorkoutSession` is a genuinely new, separate execution-record aggregate
sitting below it, matching the Bible's own two-object split even without a
`WorkoutPlan` aggregate existing yet. `WorkoutTemplate` and the Plan
Generator remain entirely out of scope.

The no-creation-event decision means any future read model needing to know
"this session was scheduled" as a discrete point in time (before it starts)
cannot rely on an event stream and must instead query `WorkoutSession`
directly by `planned_at`. This is an accepted limitation, not a gap to
silently work around — if it becomes a real requirement, adding
`WorkoutSessionPlanned` later is additive and does not change any existing
event's shape.

The `update_notes`-always-allowed decision is a real, documented behavioral
asymmetry against `Workout`/`Exercise` within the same codebase. Any future
shared "can this aggregate still be edited" abstraction across aggregates
must treat `WorkoutSession` as an explicit exception, not a bug to
normalize away.
