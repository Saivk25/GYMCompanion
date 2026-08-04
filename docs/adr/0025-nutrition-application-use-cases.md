# ADR 0025: Nutrition Application Use Cases — why Nutrition stays independent, why NutritionRuleEngine output is advisory, and why handlers never compute macros or calorie targets

- Status: accepted
- Date: 2026-07-31

## Context

Sprint 4, Phase 4 asked for the third concrete consumer of the
Application Layer Foundation (`docs/adr/0022-application-layer-
foundation.md`): six command/query handlers built on top of the single
`Nutrition` aggregate (`app.domain.nutrition`), containing "NO business
logic" of their own, orchestrating `NutritionRepository`, `UserRepository`
(when required), a `UnitOfWork`, and `NutritionRuleEngine`
(`app.domain.nutrition.rules.nutrition_rule_engine`). The task named a
fixed file list (four commands, two queries, one DTO, six handlers) and
three required ADR topics: why `Nutrition` remains an independent
aggregate, why `NutritionRuleEngine` recommendations are advisory, and
why handlers never compute macros or calorie targets.

Unlike Sprint 4, Phase 3 (`docs/adr/0024-workout-application-use-cases
.md`), this phase touches exactly one aggregate per handler — no
handler in this package loads more than one `Nutrition` entry, and only
`RecordNutritionHandler` touches a second repository (`UserRepository`,
for a referential-integrity check). `Nutrition` itself carries no
status/lifecycle (`nutrition.py`'s own module docstring: "a logged
entry... a fact captured at a point in time"), so this phase's design
questions are narrower than Phase 3's: no cross-aggregate consistency
checks, no idempotent-forward advancement, no multi-aggregate event
dispatch ordering.

One structural gap existed before `ListNutritionHandler` could be
written, resolved the same way `docs/adr/0024` resolved its own
equivalent gap for `Workout`/`WorkoutSession`: `NutritionRepository`
declared nothing beyond `get`/`add`/`remove`, and this module's own
prior docstring had already anticipated the extension ("no query method
here... is grounded in a concrete caller in this codebase yet") — this
phase is that concrete caller.

## Decision

1. **`Nutrition` remains its own, independent aggregate — not folded
   into `User`, `Workout`, or a future `NutritionPattern`/daily-rollup
   aggregate.** Three pieces of evidence support this, all already
   established before this phase and only reaffirmed by it:
   - **It has its own identity, its own repository, and its own
     lifecycle-free consistency boundary** (`docs/adr/0011-nutrition-
     is-a-per-entry-log-not-a-daily-rollup.md`): one `Nutrition` record
     is one logged entry, not a computed aggregate over other entries,
     so there is no natural parent aggregate whose invariants would
     need to span it.
   - **Nothing else in this codebase needs transactional consistency
     with a `Nutrition` entry.** `RecordNutritionHandler` is the only
     handler in this phase touching a second aggregate at all
     (`User`, read-only, for existence only) — contrast Phase 3's
     `CompleteWorkoutSessionHandler`, which had to mutate two
     aggregates in one transaction because `WorkoutSession.complete()`
     and the parent `Workout`'s state genuinely depend on each other.
     No such dependency exists between `Nutrition` and any other
     aggregate; merging it into one would import a coupling that does
     not exist in the domain.
   - **It is referenced by `user_id` only, the same "foreign key, not
     an aggregate reference" discipline every other per-user aggregate
     in this codebase already follows** (`Workout`, `Progress`,
     `Readiness`, `Goal` all carry `user_id`, never a `User` object
     reference). A future `NutritionPattern`-equivalent read model that
     rolls up multiple `Nutrition` entries into a daily total remains
     free to exist later without requiring any change to `Nutrition`
     itself — it would read `Nutrition` records via
     `list_by_user()` (decision 4), the same one-directional
     relationship `app.domain.progress.progress`'s module docstring
     describes between `Progress` and Progress Intelligence.

2. **`NutritionRuleEngine` is invoked from the Application Layer,
   immediately after a successful `commit()`, from every handler that
   mutates rule-relevant fields (`RecordNutritionHandler`,
   `UpdateNutritionHandler`, `UpdateWaterHandler`), and its output is
   surfaced only as `ApplicationResult.warnings` — never a reason to
   fail the command.** This mirrors the "evaluation-only, cannot itself
   block" discipline every rule engine wired into this codebase already
   documents for itself (`docs/adr/0018-safety-rule-engine-composition-
   and-authority.md`, `docs/adr/0024`, decision 3) — a rule engine
   evaluates deterministically over a `RuleContext` and returns
   recommendations; it never has the authority to reject a command, and
   this phase's task explicitly says so ("Do NOT fail commands because
   of advisory recommendations"). Concretely: if `HydrationRule`
   flags a `water_intake` of 500 ml as below its 1500 ml sanity
   minimum, `UpdateWaterHandler` still returns `ApplicationResult.ok(...)`
   with the warning attached — the entry was still recorded exactly as
   the caller asked; the warning is advice, not a correction. The
   small `_advisory_warnings(result: RuleResult) -> tuple[str, ...]`
   helper is duplicated in each of the three handler files rather than
   factored into a shared module, the identical "two call sites sharing
   one three-line function is not yet the second real need" reasoning
   `docs/adr/0024` gives for its own identical helper.

   `NutritionRuleContext.from_nutrition(nutrition)` is structurally
   simpler to wire in than any of Phase 3's rule-engine integrations:
   it builds directly from the just-mutated `Nutrition` aggregate, with
   no history or repository dependency at all (`context.py`'s own
   docstring — "no query method here" was never true for this
   context, it never needed one). `DeleteNutritionHandler` and the two
   read-only handlers (`GetNutritionHandler`, `ListNutritionHandler`)
   evaluate no rule engine at all: deletion removes the fact the engine
   would evaluate, and a read has nothing new to advise on that wasn't
   already advised at write time.

3. **Handlers in this package never compute macros, calorie targets,
   or any nutrition arithmetic of their own — every macro/calorie/water
   value a handler touches is a value the caller supplied (via a
   `Command`) or a value already stored on the aggregate, never a
   derived one.** `RecordNutritionHandler` passes `request.calories`,
   `request.protein`, etc. straight into `Nutrition.record(...)`
   unmodified; `UpdateNutritionHandler` passes `request.calories`, etc.
   straight into `Nutrition.update_nutrition(...)`, forwarding the
   aggregate method's own "`None` means leave unchanged" semantics
   without adding any interpretation of its own (decision 4 below).
   This is not merely convention — it is inherited directly from
   `Nutrition`'s own scope decision (`nutrition.py`'s module docstring):
   "This aggregate stores canonical nutrition information only. It does
   not compute meal plans, calorie targets, macro targets, or
   recommendations." A handler orchestrating that aggregate cannot
   introduce computation the aggregate itself was deliberately scoped
   to exclude — doing so would silently relocate business logic the
   Domain Layer explicitly declined to own into a layer whose own stated
   job (`docs/adr/0022`) is orchestration, not computation. Macro
   optimization, meal planning, and a food database are named in this
   phase's own "Do NOT implement" list for the same reason: they are
   the class of computation this scope boundary exists to keep out.

4. **`UpdateNutritionCommand`'s `None` fields mean "leave unchanged" —
   the same convention `Nutrition.update_nutrition()` itself already
   documents — not "clear," which is the opposite convention
   `UpdateWorkoutCommand` (`docs/adr/0024`) uses for `Workout`'s
   `goal`/`notes`.** This is a deliberate, non-arbitrary distinction:
   a command's job is to carry caller intent through to the aggregate
   method unmodified, and `Nutrition.update_nutrition()` already
   defines what its own `None` arguments mean before this phase ever
   existed. Inventing a different, command-level meaning for `None`
   would contradict the very method the command exists to invoke, and
   would force `UpdateNutritionHandler` to translate between two
   incompatible conventions for no benefit. `UpdateWaterCommand`, by
   contrast, makes `water_intake` a required field precisely because
   `Nutrition.update_water()` takes no optional value to interpret —
   there is nothing to leave unchanged in a single-field replace.

5. **`DeleteNutritionCommand`/`DeleteNutritionHandler` call
   `NutritionRepository.remove(nutrition)` directly — no aggregate
   method invocation, no `NutritionDeleted` event.** `Nutrition` has no
   delete or soft-delete method and `events.py` is scoped to exactly
   the four events `record()`/`update_nutrition()`/`update_water()`/
   `update_notes()` actually raise (that module's own docstring: "raise
   only what the aggregate's own methods actually do"). Because no
   aggregate method is invoked, this handler needs no `except
   DomainInvariantViolationError: raise` guard at all — unlike every
   other mutating handler in this package, there is no aggregate
   invariant to defend against, reachable or not.
   `DeleteNutritionHandler` still calls
   `self._dispatcher.dispatch(())` unconditionally on every success
   rather than special-casing "skip dispatch for this one handler" —
   `DomainEventDispatcher.dispatch(())` is explicitly documented as a
   well-defined no-op, so dispatching an empty tuple uniformly costs
   nothing and keeps every handler in this package following the same
   "commit, then dispatch" shape.

6. **`RecordNutritionHandler`'s `except DomainInvariantViolationError:
   raise` guard, and the identical guards in `UpdateNutritionHandler`/
   `UpdateWaterHandler`, are currently unreachable — kept for defensive
   consistency with every other mutating handler's "always re-raise,
   never convert" policy (`docs/adr/0023`, decision 3;
   `docs/adr/0024`, decision 6), not because any of the three paths is
   reachable today.** `Nutrition` has "no status enum and no lifecycle"
   (`nutrition.py`'s own module docstring) — none of `record()`,
   `update_nutrition()`, or `update_water()` guards a state transition
   the way `Workout._transition_to()` does, and `record()`'s only
   invariant (`ensure(recorded_at.tzinfo is not None, ...)`) is
   guaranteed by every `Clock` implementation in this codebase. All
   three guards are marked `# pragma: no cover` with an explanatory
   comment, the same convention `docs/adr/0024`, decision 6 established
   for `CreateWorkoutHandler`/`StartWorkoutSessionHandler`'s own
   currently-unreachable guards.

7. **`list_by_user(user_id) -> Sequence[Nutrition]` is added as a new
   abstract method to `NutritionRepository`, with no persistence
   implementation** — the identical "declare the contract now, implement
   it in `app.infra` later" split `docs/adr/0024`, decision 1
   established for `WorkoutRepository`/`WorkoutSessionRepository`.
   `ListNutritionHandler` is the concrete caller. The method promises no
   ordering and no rollup — it returns every entry for a user,
   unfiltered and unsummed; any date-scoping or daily-total computation
   is explicitly left to a future caller, consistent with decision 1's
   "no natural rollup aggregate exists yet" reasoning.

8. **`NutritionDTO` is a distinct type from `NutritionRuleContext`
   (`app.domain.nutrition.rules.context`), for the identical reasoning
   `docs/adr/0023`/`docs/adr/0024` give for `UserDTO`/`WorkoutDTO`
   versus their own `*Context` types.** `NutritionRuleContext` is
   scoped to `NutritionRuleEngine` only, carries six fields (no
   `nutrition_id`, `user_id`, `meal_type`, `source`, `notes`, or
   `sugar` — `context.py`'s own docstring explains the `sugar`
   omission specifically), and is never returned to a caller of this
   package. `NutritionDTO` carries every field a `GetNutritionQuery`/
   `ListNutritionQuery` caller needs, including `sugar`. Two consumers
   with different reasons to change independently stay two types.

## Consequences

Every handler in this phase — mutating or read-only — touches at most
one `Nutrition` entry per call and, other than `RecordNutritionHandler`'s
`UserRepository` existence check, at most one repository. This is the
simplest orchestration shape in the Application Layer so far, and is a
direct consequence of `Nutrition`'s own scope: no lifecycle, no
cross-aggregate dependency, no per-entry business rule beyond value
object validation. A future phase that needs `Nutrition` to interact
with another aggregate (e.g. a `NutritionPattern` daily-rollup aggregate
reading `list_by_user()`, or a Goal Alignment engine reading nutrition
history) should treat that as new evidence to revisit decision 1, not as
grounds to retroactively merge `Nutrition` into another aggregate now.

`list_by_user()` now exists on `NutritionRepository` with no persistence
behind it, the same gap `docs/adr/0024` left for
`WorkoutRepository`/`WorkoutSessionRepository` — a future infrastructure
phase adding a concrete `NutritionRepository` implementation must
support an efficient user-scoped list query alongside `get`/`add`/
`remove`.

The `# pragma: no cover` guards in decision 6 will need revisiting if a
future change gives `Nutrition` an invariant that can fail on
caller-supplied input (e.g. a future business rule constraining which
fields can be updated together) — at that point the guard becomes real
behavior with its own test, and the pragma comment should be removed
along with the coverage exclusion it documents.

## Addendum (2026-08-04): `UpdateNutritionNotesCommand`/`UpdateNutritionNotesHandler`

This phase originally shipped four commands
(`RecordNutritionCommand`/`UpdateNutritionCommand`/`UpdateWaterCommand`/
`DeleteNutritionCommand`), leaving `Nutrition.update_notes()` — a real
domain method, with its own event, `MealNotesUpdated` — unreachable
through the Application Layer. This gap surfaced during the
post-Phase-5 consistency review across Workout/Nutrition/Progress: both
sibling aggregates already exposed their own `update_notes()` at this
layer (`Workout` bundles it into `UpdateWorkoutCommand`; `Progress` has
a dedicated `UpdateNotesCommand`/`UpdateNotesHandler`,
`docs/adr/0026`), making Nutrition's omission an inconsistency rather
than a deliberate scope decision.

`UpdateNutritionNotesCommand`/`UpdateNutritionNotesHandler` close the
gap, added as a fifth command/seventh handler to this package,
following the exact shape `UpdateWaterCommand`/`UpdateWaterHandler`
established for this package's other single-field, no-optional-form
replace (decision 4): `notes: MealNotes` is required, not optional,
because `Nutrition.update_notes(notes: MealNotes, ...)` itself takes no
"leave unchanged" form. `UpdateNutritionNotesHandler` evaluates no
`NutritionRuleEngine` — `NutritionRuleContext` explicitly excludes
`notes` (that module's own docstring), the identical "not a
rule-relevant field" reasoning `docs/adr/0026`'s `UpdateNotesHandler`
gives for the same decision on `Progress`. No other decision in this
ADR changes; this addendum adds one handler to an already-accepted
shape, it does not revisit it.
