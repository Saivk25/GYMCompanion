# ADR 0007: Exercise aggregate, first increment — a global catalog node, not the graph

- Status: accepted
- Date: 2026-07-29

## Context

Sprint 2, Step 3 asked for a standalone `Exercise` aggregate: a two-state
lifecycle (`ACTIVE`, `DEPRECATED`), value objects for name/description/
instructions/muscles/equipment/contraindications, and exactly three events
(`ExerciseCreated`/`ExerciseUpdated`/`ExerciseDeprecated`) — explicitly
excluding graph traversal, progressions/regressions/alternatives, and any
relationship to `Workout`.

The Domain Model & Decision Engine Bible's closest concept is
`ExerciseGraph` (Section 4.5, Table 8): a canonical movement catalog
(`Exercise`) plus typed relationships between movements (`ExerciseRelation`
— progression/regression/substitute/antagonist-pair/accessory-of). Two
things about that table needed a decision before writing code, both
following the same pattern ADR 0005 and ADR 0006 already established:

1. `Exercise`'s own lifecycle in the Bible is four states (Draft ->
   Reviewed -> Published -> Deprecated), with a validation rule attached
   to the `Published` transition ("No Exercise may be Published without a
   reviewed, even if empty, contraindication_tags list"). The task
   explicitly asks for two states.
2. The Bible states `Exercise`'s ownership plainly: "Curated by the
   system/maintainer" and "Privacy: No personal data; this aggregate is
   shared/global, not per-user." Every aggregate built so far (`User`,
   `Workout`) is tenant-scoped — `Workout` carries a `user_id`
   specifically because the Bible's multi-tenant-from-day-one decision
   (Architecture doc Section 19) requires it. `Exercise` is the first
   aggregate where that pattern does *not* apply, and nothing in the task
   spec calls this out explicitly — it has to be inferred correctly from
   the Bible, or the natural but wrong move (copying `Workout`'s
   `user_id` field "for consistency") introduces a real bug: every
   exercise silently becoming private to whoever created it, when the
   product needs one shared library every user reads from.

Both decisions shape how the next increment (the Knowledge Graph proper,
`ExerciseRelation`, and eventually Substitution/Plan generation reading
this aggregate) must build on top of what exists today, so both get
documented here rather than left implicit.

## Decision

1. **`ExerciseStatus` is two states (`Active`/`Deprecated`), not the
   Bible's four.** The `Draft -> Reviewed -> Published` curation pipeline
   — and the "Published requires a reviewed contraindication list"
   validation rule attached to it — is not modeled. Every `Exercise` built
   through `create()` is immediately usable (`Active`); there is no
   separate review/publish workflow yet, and no curator role to perform
   one. `Contraindications` still exists as a field (defaulting to empty,
   per the Bible's own allowance), but nothing tracks whether it has been
   *reviewed* — that concept is deferred to whichever future increment
   introduces real content curation.

2. **`Exercise` carries no `user_id` and is never tenant-scoped.** It is a
   shared, global catalog aggregate, matching the Bible's "curated by the
   system/maintainer" / "shared/global, not per-user" statement exactly.
   `ExerciseRepository` (like `UserRepository`/`WorkoutRepository`) is
   still a real, correctly-typed interface, but a future Postgres
   implementation must **not** apply the row-level-security `tenant_scope`
   convention (`app/infra/database.py`) to this aggregate's table the way
   it will for `Workout` — every row is visible to every authenticated
   user by design, not a tenant-isolation gap to close later.

3. **`MovementPattern` and `Difficulty` are implemented once, as plain
   enums, resolving the task spec's own overlap** (both appear under
   "Suggested Value Objects" and, separately, under "Enums" with explicit
   members). Wrapping an enum in a second, empty value object would add
   indirection with no invariant left for it to enforce — the same
   reasoning already applied to `AccountStatus` on `User` and
   `WorkoutStatus` on `Workout`, neither of which is wrapped in a VO
   either.

4. **The primary/secondary muscle invariants live on `Exercise`, not on
   `PrimaryMuscle`/`SecondaryMuscles` individually.** Checking "no
   duplicate primary muscle" only needs `primary_muscles`; checking "a
   muscle cannot be both primary and secondary" needs both fields at once
   — no single value object can see both, so this cross-field check is the
   aggregate's job, enforced identically from `__init__` (construction and
   repository rehydration) and `update()`.

## Consequences

A future Knowledge Graph increment reconciling `Exercise` with the Bible's
full four-state lifecycle has real work to do: adding `Draft`/`Reviewed`
states before `Active` (renamed to, or merged with, `Published`), and
attaching the "reviewed contraindication list" gate to the
`Reviewed -> Published` transition specifically — not retrofitted onto
today's `create()`, which has no equivalent gate. This is an additive
migration, not a breaking one: every `Exercise` created under today's
two-state model can be treated as already `Published` once the richer
lifecycle exists.

The "no `user_id`" decision is a hard constraint the infrastructure layer
must respect when `ExerciseRepository`'s real implementation is built:
using `tenant_scope` on this aggregate's table would silently make every
user's exercise library private to them, breaking the shared-catalog
product behavior the Bible specifies. This is exactly the kind of mistake
worth pinning down in writing now, before an infrastructure increment might
otherwise copy the `Workout`/`UserAccount` pattern out of habit.

`ExerciseRelation` (the graph edges) is not started. `ExerciseRepository`
declaring no query methods beyond `get`/`add`/`remove` — the same minimal
shape as `UserRepository`/`WorkoutRepository` — means even a simple "find
all Active exercises for a MovementPattern" lookup needs a new method added
when the first real caller (Substitution or Plan generation) shows up; that
caller will very plausibly be the Knowledge Graph increment itself.
