# ADR 0021: Exercise Recommendation Rule Engine — one candidate per evaluation, composing prior engines' outputs instead of their inputs, and gate-vs-bias severity as existing `RuleResult` shape

- Status: accepted
- Date: 2026-07-30

## Context

Sprint 3, Phase 9 asked for `ExerciseRecommendationRuleEngine`:
recommending suitable exercises "by orchestrating the outputs of the
existing deterministic rule engines together with the Exercise
aggregate." Five rules were named — `ExerciseSelectionRule`,
`ContraindicatedExerciseRule`, `MovementBalanceRule`, `EquipmentRule`,
`ProgressionStageRule` — with a context that "may reference:
`ExerciseContext`, `GoalContext`, Safety results, Progressive Overload
summaries, Readiness results," explicitly noting "the application
layer is responsible for preparing the context," and an ADR
requirement to "document how recommendation rules compose the outputs
of existing rule engines without duplicating their decision logic."

The Domain Model & Decision Engine Bible's Table 48 ("Workout Rules")
names two of this phase's five rules almost literally: "Contraindication
gate — An Exercise's contraindication_tags match an active SafetyFlag —
Removed from candidates before ranking, not just deprioritized" and
"Equipment mismatch — A prescribed exercise's equipment_requirements
don't match the active Context — Auto-triggers the Substitution
workflow." A third, "Push/pull balance — Push volume exceeds pull
volume by more than the defined ratio over 7 days — Biases substitution
ranking toward pulling movements," maps to `MovementBalanceRule`. No
table entry names `ExerciseSelectionRule`'s goal-type fit or
`ProgressionStageRule`'s difficulty-vs-experience fit — both are this
phase's own scoped judgment calls.
`docs/adr/0018-safety-rule-engine-composition-and-authority.md`'s own
Consequences section had already flagged the Contraindication gate as
this future engine's job: Safety's `ContraindicationRule` "can only say
a restriction is on file, never that a specific exercise violates it."

Five design questions were specific to this phase:

1. **Every prior engine evaluates "the user's current state" once per
   call. This engine is asked to "recommend suitable exercises" —
   plural. What does one `evaluate()` call actually return?**
2. **How does composing "the outputs of the existing... rule engines"
   differ, concretely, from what Safety already did when it referenced
   `ReadinessContext`/`ProgressiveOverloadRuleContext` wholesale
   (ADR 0018)?**
3. **Table 48 distinguishes hard "removed from candidates" gates from
   soft "biases... ranking" nudges. Does this need a new field on
   `RuleResult`, or can the existing shape express it?**
4. **`ContraindicatedExerciseRule` needs the actual declared-restriction
   tag data to compare against `Exercise.contraindications.tags` — not
   just Safety's aggregate verdict. Where does that come from?**
5. **`ProgressionStageRule` needs to read Progressive Overload data
   without re-deriving Progressive Overload's own trend/plateau
   verdicts (`VolumeRule`/`IntensityRule`/`ProgressionRule`/
   `DeloadRule`). What question can it legitimately ask?**

## Decision

1. **One `ExerciseRecommendationRuleContext` evaluation answers "should
   *this one* candidate `Exercise` be recommended right now" — not
   "here is the full recommended list."** `exercise: ExerciseContext`
   is the single required field; every other field is optional
   supporting evidence. Producing an actual ranked/filtered list of
   candidates is an application-layer concern (looping over candidate
   exercises and users, calling `evaluate()` once per candidate) this
   phase does not build — consistent with the task's own explicit
   exclusion of "workout generation" and "scheduling." This mirrors
   every prior engine's own contract (`Rule.evaluate()`'s docstring:
   "evaluates this rule against `context` and returns exactly one
   `RuleResult`") rather than inventing a new one-to-many contract this
   package's rules would otherwise need.

2. **This engine composes other engines' already-computed `RuleResult`
   outputs (`safety_result`, `readiness_result`), not their raw
   contexts — a deliberate step beyond Safety's own "reference whole
   snapshots" pattern.** Safety (ADR 0018) referenced
   `ReadinessContext`/`ProgressiveOverloadRuleContext` as *inputs* and
   ran its own rules against them. This engine instead reads the
   *verdicts* those engines already reached (`RuleResult.passed`/
   `.severity`) and never re-implements any check those engines already
   perform — `ContraindicatedExerciseRule`'s CRITICAL-safety override
   reads `safety_result.severity`, it never re-evaluates readiness,
   soreness, workload, contraindication, or injury data itself; the
   `ExerciseSelectionRule` readiness nudge reads `readiness_result.
   passed`, it never re-evaluates sleep/stress/heart-rate data itself.
   This is the literal mechanism satisfying this phase's own "without
   duplicating their decision logic" ADR requirement: composing
   *outputs*, not *inputs*, is what makes duplication structurally
   impossible rather than merely avoided by discipline.
   `progressive_overload: ProgressiveOverloadRuleContext | None` is the
   one deliberate exception — see decision 5 below for why it is
   referenced as a raw context rather than a `RuleResult`.

3. **Table 48's gate-vs-bias distinction needs no new field — a
   passing `RuleResult` can already carry `recommendations`
   (`Rule._pass()`'s own docstring: "passing does not preclude offering
   advice").** `ContraindicatedExerciseRule` and `EquipmentRule` are the
   only two rules that ever call `_fail()` — matching Table 48's
   "removed from candidates before ranking" and "auto-triggers
   Substitution" language exactly, both `WARNING` severity.
   `ExerciseSelectionRule`, `MovementBalanceRule`, and
   `ProgressionStageRule` never fail — every finding they produce is a
   `_pass()` with an attached `ADVISORY` `Recommendation`, matching
   Table 48's "biases... ranking" language for the one rule it
   literally names this way, extended by this phase's own choice to
   the two rules Table 48 does not name. A caller aggregating many
   candidates' results can treat `passed=False` as "exclude" and
   `recommendations` on a passing result as "rank/prefer accordingly" —
   the exact two-tier behavior Table 48 describes, expressed entirely
   through fields `RuleResult` already had.

4. **`declared_restrictions: tuple[DeclaredRestriction, ...]` reuses
   `app.domain.safety.rules.context.DeclaredRestriction` directly,
   imported rather than redefined** — the same tag-bearing value object
   Safety's own `ContraindicationRule` already reads, supplied
   separately from `safety_result` because the *verdict* ("a
   restriction is on file") and the *raw tag data* ("which restriction,
   exactly") are genuinely different things this engine needs for two
   different purposes: `safety_result` for the broad CRITICAL override,
   `declared_restrictions` for the exercise-specific tag-intersection
   Table 48's Contraindication gate literally requires.
   `available_equipment: frozenset[EquipmentRequirement] | None`
   follows the identical reasoning for `EquipmentRule`, reusing
   `Exercise`'s own `EquipmentRequirement` type since no
   `EnvironmentContext` aggregate exists yet to source "available
   equipment" from (Domain Model & Decision Engine Bible, Section 4.3)
   — the same "supplied by the application layer, no aggregate carries
   it yet" trust `docs/adr/0020-training-load-supplied-summaries.md`
   already established for `TrainingLoadSummary`.
   `recent_movement_patterns: tuple[MovementPattern, ...]` is the one
   genuinely new concept this phase introduces: a flat occurrence tally
   (not a volume figure) `MovementBalanceRule` needs because
   `WorkoutSessionSummary` (`app.domain.workout.rules.context`) is
   deliberately whole-session granularity only (ADR 0017) and tracks no
   per-movement-pattern breakdown — a stated simplification of Table
   48's literal "push volume exceeds pull volume," documented in
   `movement_balance_rule.py`'s own docstring.

5. **`ProgressionStageRule` reads `progressive_overload.sessions`'s
   *length* — a simple, undisputed count — never its volume/intensity
   trend.** This is a different question from every rule in
   `app.domain.workout.rules`: those rules ask "is training trending
   up, plateaued, or declining"; this rule asks "how much training
   history exists at all," a fact none of Progressive Overload's own
   rules compute or expose through their `RuleResult`. Reading the same
   underlying `sessions` tuple those rules also read, for a question
   they never ask and an answer their own `RuleResult`s never carry, is
   what keeps this rule from re-implementing any of `VolumeRule`/
   `IntensityRule`/`ProgressionRule`/`DeloadRule`'s own logic — the
   session-count threshold is this rule's sole and complete opinion.

## Consequences

Any future engine that needs to "orchestrate" several prior engines'
verdicts into one higher-level decision should default to referencing
`RuleResult`s as opaque, already-computed inputs (as this engine does
for Safety and Readiness) rather than the underlying `RuleContext`s —
re-deriving a verdict from raw context data is exactly the duplication
this ADR's mechanism was built to make structurally difficult. The one
exception this phase carves out — referencing a raw context
(`ProgressiveOverloadRuleContext`) to answer a question its own rules
never ask — should be treated as narrow and rare, not a general
license to bypass `RuleResult` composition whenever convenient; each
future case should be justified as explicitly as decision 5 is here.

Because `ExerciseSelectionRule`'s goal-type fit and
`ProgressionStageRule`'s session-count thresholds are this phase's own
judgment calls rather than Bible quotations, a future increment that
adds real personalization (e.g. against `Profile.experience_level`, not
built into this context at all) should treat every default here as a
replaceable starting point — the same epistemic posture every prior
phase's own made-up thresholds carry (`VolumeRule.decline_threshold`,
`LoadRatioRule`'s ACWR bounds, and so on).

This engine produces no ranking, no candidate list, and no
Substitution workflow — only a per-candidate finding. A future
Application Layer (explicitly out of this phase's scope) is
responsible for calling this engine once per candidate `Exercise`,
collecting results, and turning "passed with recommendations" into an
actual ordered recommendation list — the gap this ADR's decision 1
names directly.
