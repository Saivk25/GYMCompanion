# ADR 0018: Safety Rule Engine — composing other engines' contexts, new restriction/injury value objects, deliberate cross-engine overlap, and evaluation-only authority

- Status: accepted
- Date: 2026-07-30

## Context

Sprint 3, Phase 6 asked for `SafetyRuleEngine`: evaluating whether it is
currently safe for a user to train, from immutable snapshots only. Five
rules were named — `ReadinessSafetyRule`, `SorenessRule`, `WorkloadRule`,
`ContraindicationRule`, `InjuryRule` — with a context that "may include:
`ReadinessContext`, `ProgressiveOverloadRuleContext` summaries,
`GoalContext` (when needed), `UserContext` (only immutable restriction
data if applicable)."

The Domain Model & Decision Engine Bible treats Safety as the system's
highest-authority engine: Section 10.4 calls it "the highest-authority
engine in the system — can override any other engine; is overridden by
none," and its own decision-authority table (Section 8, Table 41) marks
"Safety / escalation go-no-go" as "Rules, exclusively — the only layer
permitted to decide." The Bible's own safety data model
(`SafetyFlag`, `EscalationCase`, `pain_flags`/`GI_symptoms` on
`ReadinessCheckIn`/`WorkoutSession`) is richer than anything this
codebase has built: no `SafetyFlag` aggregate exists yet (the
`UserProfile` docstring already documents that omission), and
`ReadinessContext` carries no `pain_flags`/`GI_symptoms` fields (the
Readiness README entry already documents that omission too).

Four design questions were specific to this phase:

1. **How does a context compose data this codebase has never combined
   before — another engine's context type, a second engine's context
   type, and data no aggregate carries at all?**
2. **Where does "declared movement restriction" / "active injury" data
   come from, given no `SafetyFlag` aggregate exists?**
3. **`SorenessRule` reads the same `ReadinessContext.soreness_level`
   field `app.domain.readiness.rules.soreness_rule.SorenessRule`
   already evaluates, and `WorkloadRule` reads the same
   `WorkoutSessionSummary.total_volume` data
   `app.domain.workout.rules.deload_rule.DeloadRule` already evaluates.
   Is this a problem?**
4. **What does "highest-authority engine... overridden by none" actually
   mean for a package that has no visibility into any other engine's
   `RuleResult`?**

## Decision

1. **`SafetyRuleContext` references other engines' whole context types —
   `readiness: ReadinessContext | None` and `recent_training:
   ProgressiveOverloadRuleContext | None` — rather than flattening their
   fields.** The same "reference whole snapshots" shape ADR 0016
   established for `GoalAlignmentRuleContext`, for the same reason:
   `ReadinessSafetyRule`/`SorenessRule` need most of what
   `ReadinessContext` already carries, and `WorkloadRule` needs the full
   `sessions` history `ProgressiveOverloadRuleContext` already holds, not
   a small fixed subset. No `GoalContext` field, even though the task
   named it as a "may include... when needed" option: none of this
   package's five rules need goal data to decide whether it's currently
   safe to train, so adding the field would repeat the exact mistake
   `NutritionRuleContext`'s own docstring already warns against (no
   `sugar` field there, because no rule reads it). A future rule that
   genuinely needs goal-aware safety context can add it when that rule
   is written — the field's absence today is a scoping decision, not an
   oversight.

2. **`DeclaredRestriction` and `ActiveInjury` are two small, new value
   objects, defined in this package, holding whatever a caller already
   knows.** No `SafetyFlag` aggregate exists to source this data from,
   the same situation Progressive Overload faced with no existing
   volume/intensity summary type (ADR 0017) — this phase's own task
   explicitly says these two rules evaluate restrictions/injuries
   "supplied in the context," which is exactly what these two types are
   for. `SafetyRuleContext.declared_restrictions`/`active_injuries` both
   default to an empty tuple, which is treated as a real, confirmed fact
   ("none declared") distinct from `readiness`/`recent_training`'s `None`
   default (genuinely "not supplied, cannot evaluate") — an empty
   restriction/injury list is not the same claim as a missing readiness
   check-in.

3. **Two rules deliberately re-evaluate a field another engine already
   reads, at a different threshold and severity, and this is not a
   duplication bug.** `SorenessRule` here uses a stricter threshold (9,
   versus Readiness's own advisory `SorenessRule`'s 7) and CRITICAL
   severity (versus WARNING) — it answers "is this severe enough that
   training is unsafe," not "here's some general advice." `WorkloadRule`
   answers a genuinely different question from `DeloadRule` besides just
   reusing the same field: `DeloadRule` (Progressive Overload, ADVISORY)
   flags *sustained* near-peak volume with no lighter session — a
   training-quality signal. `WorkloadRule` (Safety, WARNING) flags a
   *sudden spike* relative to a recent baseline — a "too much, too soon"
   injury-risk pattern, loosely related to the sports-science
   acute:chronic workload ratio concept though computed here as a
   simpler two-window average ratio, not a true exponentially-weighted
   ACWR (a stated simplification). Two engines holding independent
   opinions about the same underlying data, each for its own engine's
   purpose, is the same "independent rules, no shared state" posture ADR
   0014 established within one engine's own rule set — this phase
   extends it across engine boundaries rather than introducing a new
   principle.

4. **This engine's authority is evaluation-only, not enforcement.** It
   computes what a caller should know, as conservatively as its inputs
   allow (`InjuryRule` and `ReadinessSafetyRule` default to CRITICAL,
   the most severe defaults in this codebase so far). It cannot block a
   `WorkoutSession`, override a `ProgressiveOverloadRuleContext`
   `RuleResult`, or gate `Plan` activation — nothing in `app/domain` at
   this phase has a mechanism for one engine's output to suppress
   another's, and building that mechanism (Bible Section 8.4's
   Arbitration stage; Section 8.3's "Rule layer and AI layer disagree:
   Rule layer always wins") is an application-layer concern this phase
   does not build. "Highest authority" here means: when a future
   application layer does combine this engine's output with others', it
   should treat this engine's CRITICAL findings as the one that always
   wins the arbitration — a contract this ADR states for that future
   consumer to honor, not a runtime enforcement this package performs
   itself.

## Consequences

Any future rule engine that needs "is it currently safe to do X" should
default to this same composition shape — reference other engines'
context types whole, add new small value objects only for data no
aggregate carries yet, and treat an empty collection as a confirmed fact
rather than missing data — rather than re-flattening fields a sibling
engine's context already exposes.

Because `ReadinessSafetyRule` cannot see the Bible's `pain_flags`/
`GI_symptoms` fields (neither exists on `ReadinessContext`), it is not a
literal implementation of the Bible's red-flag override (Table 50) —
only this codebase's nearest deterministic equivalent given what
`ReadinessContext` actually has (sleep, stress, resting heart rate,
HRV). If a future increment adds `pain_flags`/`GI_symptoms` to
`Readiness` (closing the gap the Readiness README already names), this
rule should be revisited to read them directly rather than only inferring
distress from sleep/stress/heart-rate proxies.

`ContraindicationRule` can only say a restriction is on file, never that
a specific exercise violates it — a real, exercise-selection-level
`Exercise.contraindication_tags` gate (Bible Table 48) remains future
scope for an Exercise Recommendation/Substitution engine, explicitly out
of this phase. `InjuryRule` similarly cannot block a session from being
created or started; a future Plan/Session-generation increment
implementing the Bible's `EscalationCase` gate ("blocks high-intensity
Session tiers and new Plan activation until resolved") would need to
actually read this engine's `RuleResult` and act on it — this phase only
produces the finding.
