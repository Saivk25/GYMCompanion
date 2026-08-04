# ADR 0027: Readiness Application Use Cases — why Readiness stays independent, why ReadinessRuleEngine output is advisory, and why UpdateNotesCommand shipped from day one this time

- Status: accepted
- Date: 2026-08-05

## Context

Sprint 4, Phase 6 is the fifth concrete consumer of the Application
Layer Foundation (`docs/adr/0022-application-layer-foundation.md`):
seven command/query handlers built on top of the single `Readiness`
aggregate (`app.domain.readiness`), containing no business logic of
their own, orchestrating `ReadinessRepository`, `UserRepository` (when
required), a `UnitOfWork`, and `ReadinessRuleEngine`
(`app.domain.readiness.rules.readiness_rule_engine`).

This phase follows immediately after a Principal-Engineer-level
consistency review of the Application Layer as built through Phase 5
(Workout, Nutrition, Progress). That review found no Critical issues
and approved proceeding, but surfaced one concrete, non-speculative gap:
`Nutrition.update_notes()` had shipped in Phase 4 with no Application
Layer exposure at all, closed afterward as a small, isolated cleanup
(see the addendum in `docs/adr/0025-nutrition-application-use-cases
.md`). This phase's own `UpdateNotesCommand`/`UpdateNotesHandler` for
`Readiness.update_notes()` therefore ships as part of the phase's
original scope, not as a follow-up fix — see decision 5.

`Readiness` carries no status/lifecycle (`readiness.py`'s own module
docstring: "a check-in is a fact captured at a point in time"), the
same shape `Nutrition`/`Progress` already established. Its four
aggregate methods (`record()`, `update_sleep()`,
`update_recovery_metrics()`, `update_notes()`) map directly onto five
commands (the fifth, `DeleteReadinessCommand`, has no aggregate-method
counterpart — see decision 6) plus two read queries.

## Decision

1. **`Readiness` remains its own, independent aggregate — not folded
   into `User` or a future `RecoveryState` aggregate.** The same three
   pieces of evidence `docs/adr/0025`'s decision 1 gives for
   `Nutrition` apply here: `Readiness` has its own identity, its own
   repository, and its own lifecycle-free consistency boundary
   (`readiness.py`'s module docstring: a check-in is a fact, not a
   computed rollup); nothing else in this codebase needs transactional
   consistency with a `Readiness` check-in
   (`RecordReadinessHandler`'s `UserRepository` check is read-only,
   existence-only); and it is referenced by `user_id` only, the same
   "foreign key, not an aggregate reference" discipline every other
   per-user aggregate in this codebase follows. A future `RecoveryState`
   aggregate — "the rolling, derived state built from a window of
   check-ins plus training load," `readiness.py`'s own module docstring
   names this as a deliberately separate, not-yet-built concept — would
   read `Readiness` records via `list_by_user()` (decision 4), the same
   one-directional relationship every other aggregate's own Progress
   Intelligence/rollup-reader precedent already establishes. This
   phase's task is explicit that this increment "does not compute a
   readiness score, a recovery band, deload triggers" — that scope
   boundary is inherited unchanged from the Domain Layer, not invented
   here.

2. **`ReadinessRuleEngine` is invoked from the Application Layer,
   immediately after a successful `commit()`, from every handler that
   mutates rule-relevant fields (`RecordReadinessHandler`,
   `UpdateSleepHandler`, `UpdateRecoveryMetricsHandler`), and its
   output is surfaced only as `ApplicationResult.warnings` — never a
   reason to fail the command.** This is the identical
   "evaluation-only, cannot itself block" discipline every rule engine
   wired into this codebase already documents for itself
   (`docs/adr/0018`, `docs/adr/0024` decision 3, `docs/adr/0025`
   decision 2). `ReadinessRuleContext.from_readiness(readiness)` is
   built directly from the just-mutated aggregate, with no history or
   repository dependency — the identical shape
   `NutritionRuleContext.from_nutrition()` uses (`docs/adr/0025`), and
   structurally simpler than `ProgressEvaluationRuleContext`'s
   full-history rebuild (`docs/adr/0026`), because none of
   `SleepRule`/`EnergyRule`/`StressRule`/`SorenessRule`/`RecoveryRule`
   is trend-based — each evaluates one check-in's own fields in
   isolation (`context.py`'s own docstring). `UpdateNotesHandler` and
   `DeleteReadinessHandler` evaluate no rule engine at all: notes are
   explicitly excluded from `ReadinessRuleContext`, and deletion
   removes the fact the engine would evaluate. `GetReadinessHandler`/
   `ListReadinessHandler` are read-only and evaluate nothing new.

3. **Handlers in this package never derive a readiness score, recovery
   band, or deload recommendation of their own — every sleep/recovery
   value a handler touches is a value the caller supplied (via a
   `Command`) or a value already stored on the aggregate, never a
   computed one.** This is inherited directly from `Readiness`'s own
   scope decision (`readiness.py`'s module docstring: "This increment
   stores observations only... Future rule engines consume these
   records; none are implemented here" beyond the five already-built
   advisory rules). `RecordReadinessHandler` passes
   `request.sleep_duration`, `request.energy_level`, etc. straight into
   `Readiness.record(...)` unmodified; `UpdateSleepHandler`/
   `UpdateRecoveryMetricsHandler` forward `Readiness.update_sleep()`/
   `update_recovery_metrics()`'s own "`None` means leave unchanged"
   semantics without adding interpretation of their own (decision 4).
   `RecoveryState` derivation, deload triggers, and any windowed/
   trend-based readiness score are named out of scope by the same
   reasoning that keeps macro computation out of the Nutrition
   Application Layer (`docs/adr/0025` decision 3).

4. **`UpdateSleepCommand`'s and `UpdateRecoveryMetricsCommand`'s
   `None` fields mean "leave unchanged" — the same convention
   `Readiness.update_sleep()`/`update_recovery_metrics()` themselves
   already document, matching `UpdateNutritionCommand`'s convention
   (`docs/adr/0025` decision 4), not `UpdateWorkoutCommand`'s opposite
   "clear" convention (`docs/adr/0024`).** A command's job is to carry
   caller intent through to the aggregate method it invokes unmodified;
   `Readiness.update_sleep()`/`update_recovery_metrics()` already
   define what their own `None` arguments mean before this phase ever
   existed, so neither command invents a different, command-level
   meaning.

5. **`UpdateNotesCommand`/`UpdateNotesHandler` ship as part of this
   phase's original five commands/seven handlers, not added
   afterward.** Every prior phase exposed its aggregate's
   `update_notes()`-equivalent method inconsistently: Workout bundles
   notes into `UpdateWorkoutCommand`; Progress has a dedicated
   `UpdateNotesCommand` from its own Phase 5; Nutrition shipped Phase 4
   with no exposure at all, caught only by the subsequent consistency
   review and closed as a follow-up (`docs/adr/0025`'s addendum). That
   review's own explicit finding — a real domain capability left
   unreachable through the Application Layer is a functional gap, not
   a style choice — is the direct cause of this decision: every
   aggregate's `update_notes()` now gets its own command/handler from
   the start of its own phase, closing the door on a sixth phase
   repeating Nutrition's gap. `UpdateNotesHandler` evaluates no
   `ReadinessRuleEngine` (decision 2) — the same "not a rule-relevant
   field" reasoning `docs/adr/0026`'s `UpdateNotesHandler` documents for
   `Progress`.

6. **`DeleteReadinessCommand`/`DeleteReadinessHandler` call
   `ReadinessRepository.remove(readiness)` directly — no aggregate
   method invocation, no `ReadinessDeleted` event.** `Readiness` has no
   delete or soft-delete method and `events.py` is scoped to exactly
   the four events `record()`/`update_sleep()`/
   `update_recovery_metrics()`/`update_notes()` actually raise, the
   identical "raise only what the aggregate's own methods actually do"
   discipline `docs/adr/0025` decision 5 documents for
   `DeleteNutritionHandler`. Because no aggregate method is invoked,
   this handler needs no `except DomainInvariantViolationError: raise`
   guard at all. `DeleteReadinessHandler` still calls
   `self._dispatcher.dispatch(())` unconditionally on every success —
   `DomainEventDispatcher.dispatch(())` is a well-defined no-op, so
   dispatching an empty tuple uniformly costs nothing and keeps every
   handler in this package following the same "commit, then dispatch"
   shape.

7. **Every `except DomainInvariantViolationError: raise` guard in this
   package's mutating handlers is currently unreachable — kept for
   defensive consistency with every other mutating handler's "always
   re-raise, never convert" policy** (`docs/adr/0023` decision 3,
   `docs/adr/0024` decision 6, `docs/adr/0025` decision 6, `docs/adr/
   0026` decision 6), not because any path is reachable today.
   `Readiness` has "no status enum and no lifecycle"
   (`readiness.py`'s own module docstring) — none of `record()`,
   `update_sleep()`, `update_recovery_metrics()`, or `update_notes()`
   guards a state transition, and `record()`'s only invariant
   (`ensure(recorded_at.tzinfo is not None, ...)`) is guaranteed by
   every `Clock` implementation in this codebase. All four guards are
   marked `# pragma: no cover` with an explanatory comment, the same
   convention every prior phase established.

8. **`list_by_user(user_id) -> Sequence[Readiness]` is added as a new
   abstract method to `ReadinessRepository`, with no persistence
   implementation** — the identical "declare the contract now,
   implement it in `app.infra` later" split `docs/adr/0024` decision 1,
   `docs/adr/0025` decision 7, and `docs/adr/0026` decision (`Progress`)
   already established for their own repositories.
   `ListReadinessHandler` is the concrete caller. The method promises
   no ordering; it does not, by itself, enforce the Bible's "one
   check-in per day" rule (still a future application/repository-layer
   concern — `readiness.py`'s own module docstring already anticipated
   this).

9. **`ReadinessDTO` is a distinct type from `ReadinessContext`
   (`app.domain.readiness.context`), for the identical reasoning
   `docs/adr/0025` decision 8 gives for `NutritionDTO` versus
   `NutritionContext`.** `ReadinessContext` is scoped to a future
   domain service (`RecoveryState` derivation, the Safety Rule Engine —
   neither built yet), one-directional, and never crosses the
   Application Layer boundary; `ReadinessDTO` is this layer's own read
   projection for `GetReadinessHandler`/`ListReadinessHandler`, a
   different consumer with different reasons to change independently.

10. **The `_advisory_warnings()` helper is duplicated a third, fourth,
    and fifth time in this phase** (`RecordReadinessHandler`,
    `UpdateSleepHandler`, `UpdateRecoveryMetricsHandler`), bringing the
    running total to 11 identical copies across Workout/Nutrition/
    Progress/Readiness. `docs/TECH_DEBT.md`'s TD-0001 — opened during
    the post-Phase-5 consistency review, before this phase started —
    already names "a 9th call site is added" as one of its explicit
    extraction triggers; this phase's three new call sites cross that
    threshold. Extraction is still **not** performed in this phase:
    this phase's own task is explicit that it should "maintain the
    current architecture" and "not redesign anything," so introducing
    a new shared module mid-phase would itself be a scope violation of
    that instruction, not a fix. TD-0001's status and count are updated
    to reflect the new total and the fact its own trigger has now
    fired; the extraction itself is left as an explicit follow-up
    decision for the next unit of work, not silently deferred again.

## Consequences

This phase's orchestration shape sits between Nutrition's (Phase 4,
simplest so far — no history, no cross-aggregate lifecycle) and
Progress's (Phase 5, full-history rule context): `Readiness` shares
Nutrition's "rebuild the rule context from the just-mutated aggregate
alone, no repository read needed" shape, not Progress's "rebuild from
the user's full history" one, because none of this phase's five rules
is trend-based.

`list_by_user()` now exists on `ReadinessRepository` with no
persistence behind it, matching the same gap left open on
`WorkoutRepository`/`NutritionRepository`/`ProgressRepository` — a
future infrastructure phase adding a concrete `ReadinessRepository`
implementation must support an efficient user-scoped list query
alongside `get`/`add`/`remove`, and should also consider whether
enforcing "one check-in per day" belongs at that layer (still an open
question this phase deliberately leaves open, per `readiness.py`'s own
module docstring).

`docs/TECH_DEBT.md`'s TD-0001 (`_advisory_warnings()` duplication) now
sits at 11 call sites, past its own stated 9-call-site extraction
trigger. The next phase (Goal Application Use Cases, or whichever unit
of work follows) should treat resolving TD-0001 — either by extracting
the shared helper or by explicitly re-justifying continued deferral —
as a required decision before adding a 12th copy, not an optional
cleanup.

The `# pragma: no cover` guards in decision 7 will need revisiting
under the identical condition every prior phase's ADR already names: a
future change giving `Readiness` an invariant that can fail on
caller-supplied input.
