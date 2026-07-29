# ADR 0014: Readiness Rule Engine — five independent rules composed by the shared RuleEngine, not one monolithic evaluator

- Status: accepted
- Date: 2026-07-30

## Context

Sprint 3, Phase 2 asked for the first concrete deterministic rule engine,
`ReadinessRuleEngine`, built on the Phase 1 Rule Engine foundation
(`app.domain.rules`, ADR 0013) and the Readiness aggregate. Five named
rules — `SleepRule`, `EnergyRule`, `StressRule`, `SorenessRule`,
`RecoveryRule` — each evaluate one or two fields of a new
`ReadinessRuleContext`. The task explicitly asked this ADR to document
"the rule composition strategy and why independent rules are preferred
over one monolithic evaluator" — i.e., the central design question this
phase poses is not "what do the rules check" but "how many `Rule`
subclasses should this engine have."

The alternative to five small `Rule` subclasses is one `Rule` (or, more
likely, no `Rule` abstraction at all — just a plain function) that reads
every field of `ReadinessRuleContext` and returns a single `RuleResult`
covering sleep, energy, stress, soreness, and recovery metrics together.
Both approaches can satisfy the task's literal ask ("evaluates a user's
readiness ... produces deterministic recommendations"); the choice
between them is an architectural one with consequences for every rule
engine built after this one, which is exactly why Phase 1's `Rule` and
`RuleEngine` (ADR 0013) were built as *composable* primitives rather than
a single opaque `evaluate(context) -> RuleResult` function in the first
place.

## Decision

**Five independent `Rule[ReadinessRuleContext]` subclasses, composed by
one `ReadinessRuleEngine` (a thin, behavior-preserving configuration of
the shared `RuleEngine`, per ADR 0013's own guidance).** Concretely:

1. **Each rule owns exactly one concern and is independently
   constructible, testable, and configurable.** `SleepRule`,
   `EnergyRule`, `StressRule`, and `SorenessRule` each take their own
   threshold and severity as constructor parameters with sensible
   defaults; `RecoveryRule` takes two (resting heart rate ceiling, HRV
   floor) because it is the one rule the task named as covering two
   fields ("Evaluate resting heart rate and HRV"). A test for
   `SleepRule` never has to construct energy, stress, soreness, or
   recovery data it doesn't care about — each rule's test file is
   self-contained, unlike a monolithic evaluator's test suite, which
   would need a fully-populated context for every case regardless of
   which single field that case is actually about.

2. **A single failing check never blocks or short-circuits evaluation of
   the others.** `RuleEngine.evaluate()` (ADR 0013) always runs every
   rule and aggregates all results — a user who slept badly *and* is
   stressed gets both findings, not just the first one a monolithic
   `if`/`elif` chain happened to check first. This is a direct
   consequence of composing via the shared `RuleEngine` rather than
   writing bespoke branching logic inside one evaluator.

3. **Every rule treats a missing input the same way: pass, not fail.**
   `Readiness`'s own fields are all optional (nothing in `Readiness.
   record()` requires any of them), so a context missing, say,
   `resting_heart_rate` is a normal, expected shape, not a data-quality
   problem — the same "insufficient data is not an error" posture ADR
   0013's own `RuleContext` design and the Bible's confidence-tier
   philosophy (Section 8.4) both take for missing inputs generally. A
   monolithic evaluator would need this same "if present, check it;
   otherwise skip" guard repeated five times inline, in one long method,
   with no boundary stopping a bug in the sleep-checking logic from
   corrupting a variable the stress-checking logic also reads later in
   the same function body — independent `Rule` instances have no shared
   mutable state to corrupt across concerns in the first place.

4. **Adding, removing, or reconfiguring one check is a one-file,
   one-class change.** A future increment tuning `EnergyRule`'s minimum
   threshold, or adding a sixth rule (say, a hydration check once
   `Nutrition`'s `WaterIntake` is wired in), touches exactly one new or
   existing file and one line in `_default_rules()` — never a shared
   `evaluate()` method every other check also lives inside.

Two smaller decisions that follow from composing via the existing
`RuleEngine` rather than writing bespoke logic:

- **`ReadinessRuleContext` carries only the six fields these five rules
  read** — not the full `Readiness` aggregate, and not the broader
  `ReadinessContext` read-model that already exists for other consumers
  (`app.domain.readiness.context`). A rule should not be able to reach
  for `readiness_id` or `notes` it has no business inspecting; keeping
  the context minimal makes that structurally true, not just a
  convention.
- **`ReadinessRuleEngine` subclasses `RuleEngine[ReadinessRuleContext]`
  purely for a discoverable name and a zero-argument default
  constructor** (wiring up the five default rules) — it overrides no
  method and adds no behavior, honoring ADR 0013's "an instance of
  `RuleEngine`, not a subclass overriding its behavior" guidance in
  spirit: the override here is configuration, not semantics.

## Consequences

Every future rule engine in this codebase (Workout Rules, Safety Rules,
and the rest of the Bible's nine) should default to this same shape
unless a concrete reason argues otherwise: many small, single-concern
`Rule` subclasses per context field or closely related field group,
composed by one thin `XyzRuleEngine(RuleEngine[XyzRuleContext])`. A
"why is this one `Rule` checking five unrelated things" review question
should be treated as a real design smell going forward, not a style
nitpick.

The fixed numeric thresholds each rule defaults to (7 hours of sleep,
energy/stress/soreness at 4/7/7 out of 10, 70 bpm resting heart rate, 40 ms
HRV) are this phase's own general-purpose defaults, not figures the Bible
mandates and not tuned to any individual user's own baseline — every
rule's constructor accepts an override specifically so a future increment
(e.g., an experience-tier- or profile-aware readiness engine) can supply
different thresholds without touching this package's logic at all, only
its configuration.

Because `RecoveryRule` is the one rule spanning two fields, it is also
the one place a future contributor might be tempted to add a third,
fourth, or combined metric "since it's already in there." That temptation
should be resisted past the point of "closely related raw observations
evaluated independently" (what `RecoveryRule` does today) into "a
derived score or index" (what `RecoveryState` will do) — the line this
phase's own Do Not list draws between "Recovery Rules" and "recovery
score."
