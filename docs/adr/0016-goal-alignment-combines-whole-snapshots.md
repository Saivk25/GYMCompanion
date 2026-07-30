# ADR 0016: Goal Alignment Rule Engine — whole-snapshot context, explicit reference date, and a shared "Active goals only" policy

- Status: accepted
- Date: 2026-07-30

## Context

Sprint 3, Phase 4 asked for the first rule engine spanning two
aggregates: `GoalAlignmentRuleEngine`, evaluating whether a user's
current state aligns with an active goal. `GoalAlignmentRuleContext`
"may reference immutable snapshots from: Goal, Progress" — both already
have existing snapshot types (`GoalContext`, `ProgressContext`) built
during Sprint 2. Five rules were named — `TargetDateRule`,
`BodyWeightRule`, `BodyFatRule`, `StrengthGoalRule`, `PriorityRule` —
each evaluating a different dimension of one goal.

Three design questions were specific to this phase, not already answered
by ADR 0013 (Rule Engine foundation), ADR 0014 (independent-rule
composition), or ADR 0015 (range thresholds):

1. **How should the context combine two aggregates' data?**
   `ReadinessRuleContext` and `NutritionRuleContext` (Phases 2 and 3)
   each flatten their *single* source aggregate's relevant fields
   directly into new context fields. Goal Alignment has two source
   aggregates and needs almost everything each one's own existing
   snapshot type already carries.

2. **`TargetDateRule` needs "today."** No context field in either prior
   phase needed a notion of "the current date" — every Readiness and
   Nutrition rule compared a logged value against a fixed numeric
   threshold. `TargetDateRule` must compare `target_date` against
   *when the evaluation happens*, which is not data the goal or the
   progress snapshot carries on its own.

3. **What does "not applicable" mean across five different dimensions?**
   A completed, cancelled, or expired goal has no meaningful "is the
   target date approaching," "is body weight aligned," or "is this a
   high priority to act on" — but each of the five rules could, in
   isolation, invent its own answer to "what do I do with a non-Active
   goal" without any shared rule enforcing consistency.

## Decision

1. **`GoalAlignmentRuleContext` holds whole `GoalContext` and
   `ProgressContext | None` values, not flattened individual fields.**
   `context.goal.target_weight`, not a bare `target_weight` field
   duplicated onto this context. This is a deliberate departure from the
   Readiness/Nutrition contexts' flattening pattern, not an
   inconsistency: those contexts each needed a small, fixed subset of
   one aggregate's fields (5-6 fields), and flattening kept "does this
   context contain more than a rule needs" trivially checkable. Goal
   Alignment needs almost every field either snapshot type already
   exposes (`target_date`, `target_weight`, `target_body_fat`,
   `target_strength`, `priority`, `status` from `Goal`; `body_weight`,
   `body_fat_percentage` from `Progress`) — re-declaring nearly the same
   field list a second time under new names would be pure duplication of
   structure `GoalContext`/`ProgressContext` already provide, with no
   corresponding benefit. `progress` stays `Optional` (not every goal
   evaluation has a recent check-in to compare against) the same way
   every optional field in every prior context is `Optional`.

2. **`reference_date` is an explicit, required context field, never a
   `date.today()` call inside a rule.** `Rule.evaluate()`'s own contract
   (ADR 0013) requires "no wall-clock reads" for exactly this reason: a
   rule that read the system clock internally would stop being a pure
   function of its context, and the same context evaluated on two
   different days would silently produce two different
   `TargetDateRule` results — a real violation of "deterministic," not
   just a style concern. `GoalAlignmentRuleContext.from_aggregates()`
   takes a `Clock` (the shared kernel's own testable time abstraction,
   already used by every aggregate factory in this codebase) and stamps
   `reference_date` from it once, at context-construction time, so
   every rule inside one `evaluate()` call sees the same "today."

3. **All five rules independently apply the same guard: a goal that is
   not `GoalStatus.ACTIVE` always passes, with an explanation naming its
   actual status.** Not enforced by a shared base class or mixin — each
   rule's own `evaluate()` checks `goal.status is not GoalStatus.ACTIVE`
   first, the same "no shared mutable state between rules, small
   duplication is fine" posture ADR 0014 already established for
   Readiness's rules. This keeps every rule's "not applicable" case
   consistent across all five dimensions without introducing a coupling
   mechanism (inheritance, a template method) between otherwise
   independent rules.

One smaller, colocated decision: `BodyWeightRule` compares
`Progress.body_weight`'s raw numeric value against
`Goal.target_weight`'s raw numeric value with no unit reconciliation —
`Goal.target_weight` carries no `MeasurementUnit` of its own (its own
docstring already says "in whatever unit the caller has agreed with the
user"), while `Progress.body_weight` is always paired with one on the
same record. This rule does not attempt to convert between units; it is
documented as a known, stated limitation in `body_weight_rule.py`'s own
module docstring, not silently assumed. `BodyFatRule` has no equivalent
caveat: both `TargetBodyFat` and `BodyFatPercentage` are unambiguously
0-100 percentages with no unit variant.

## Consequences

Any future rule engine that needs to combine data from two or more
aggregates (nothing else in this codebase does yet) should default to
this same "reference whole existing snapshot types" shape when it needs
most of what each aggregate's snapshot already exposes, and only fall
back to Readiness/Nutrition's flatten-to-a-few-fields shape when it
genuinely needs just a handful of one aggregate's fields. Neither shape
is universally "more correct" — the right choice depends on how much of
the source snapshot the rules actually use, and both remain valid
patterns in this codebase going forward.

Because `reference_date` must be supplied explicitly, any future
extension of this engine (or a new one needing "now") should follow the
same convention — accept a `Clock` at context-construction time, never
read the system clock from inside a `Rule.evaluate()` — to preserve every
rule's determinism guarantee.

A real fix for `BodyWeightRule`'s unit mismatch would require either
adding a `MeasurementUnit` to `Goal.target_weight` (a change to the Goal
aggregate itself, out of scope for a rule-engine phase) or converting
units at the point `GoalAlignmentRuleContext` is assembled. Neither is
implemented here; a future increment that actually needs unit-safe
comparison should treat this as real, scoped work, not something this
rule already silently handles.

`StrengthGoalRule` — which can never trigger in this phase, since
`GoalAlignmentRuleContext` carries no strength/lift performance data at
all — is a deliberate placeholder acknowledging where a future
`WorkoutSession`/`ExercisePerformance`-backed data source would need to
be added to this context (and, likely, this rule rewritten to actually
compare progress) once that data becomes available. Adding that data
source is real, new scope, not a bug fix to this rule.
