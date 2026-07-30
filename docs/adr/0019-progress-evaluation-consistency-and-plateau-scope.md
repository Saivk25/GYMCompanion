# ADR 0019: Progress Evaluation Rule Engine — hybrid context shape, the first deliberate fail-on-missing-data rule, and plateau/measurement-trend scope

- Status: accepted
- Date: 2026-07-30

## Context

Sprint 3, Phase 7 asked for `ProgressEvaluationRuleEngine`: evaluating
whether a user's historical body-composition and measurement trends are
progressing toward active goals, from immutable snapshots only. Five
rules were named — `BodyWeightRule`, `BodyFatRule`,
`MeasurementTrendRule`, `ConsistencyRule`, `PlateauRule` — with a
context that "may include: `ProgressContext` history, `GoalContext`,
Reference date."

The Domain Model & Decision Engine Bible's Section 10.7 ("Progress
Rules") scopes what trend/plateau/forecast claims are allowed to be
shown, and Table 54 states two rules this phase had to translate into
code: a "Minimum evidence rule" (the UI must show "not enough data yet"
instead of a line when evidence is insufficient) and a "Plateau
definition" requiring "a defined number of consecutive flat weeks — a
single flat week is never a plateau."

Four design questions were specific to this phase:

1. **This is the first context that needs both a *history* of snapshots
   (the shape ADR 0017 established for Progressive Overload) and a
   *whole referenced snapshot* (the shape ADR 0016 established for Goal
   Alignment) at the same time. How should both coexist in one context?**
2. **Every rule engine built so far follows "missing data passes, never
   fails" (ADR 0014 and every ADR since). Table 54's "Minimum evidence
   rule" reads as a direct instruction to do the opposite for
   consistency. Is this actually a Bible-grounded exception, or an
   inconsistency to avoid?**
3. **`Progress` has no lifecycle/status field (ADR 0010) and the domain
   model has no weekly cadence for progress entries — how should
   "consecutive flat weeks" be approximated?**
4. **`MeasurementTrendRule` covers nine fields (waist, chest, hip, arm,
   thigh, calf, neck, lean body mass, muscle mass) with no `Goal` target
   for any of them. What should "fail" mean here, if anything?**

## Decision

1. **`ProgressEvaluationRuleContext` carries both shapes at once:
   `progress_history: tuple[ProgressContext, ...]` (history, ADR 0017's
   shape) and `goal: GoalContext | None` (whole-snapshot reference, ADR
   0016's shape).** This is the first context in the codebase to
   genuinely need both simultaneously: `BodyWeightRule`/`BodyFatRule`
   compare a *trend across history* against a *goal's target*, which
   needs both shapes at once rather than either alone. `reference_date:
   date` is also included, non-optional, sourced from `Clock` only in
   `from_aggregates()` — but unlike Goal Alignment (every rule reads
   it) or Progressive Overload (no rule needs it), this package is a
   deliberate middle case: only `ConsistencyRule` actually reads it, to
   judge staleness of the latest entry relative to "now." The field's
   presence is not assumed to imply every rule uses it — that
   assumption is explicitly rejected in this ADR so future readers do
   not treat "this context has `reference_date`" as shorthand for "every
   rule here needs today's date."

2. **`ConsistencyRule` deliberately fails (not passes) when progress
   entries are too few or too stale — the first rule in the entire
   codebase to make this choice.** Every rule engine built before this
   phase (Readiness, Nutrition, Goal Alignment, Progressive Overload,
   Safety, and every other rule in this same Progress Evaluation
   package) treats missing/insufficient data as "cannot evaluate,"
   returning a pass with an explanation, per the task's own standing
   instruction. This phase's task text supplied its own escape hatch —
   "unless the Product Bible explicitly specifies otherwise" — and
   Table 54's "Minimum evidence rule" is read as exactly that
   specification: the Bible does not merely say trend claims are
   *uncertain* with too little data, it says the UI "must show 'not
   enough data yet' instead of a line," i.e. the absence of a
   trend-worthy line is itself the required signal, not an optional
   footnote. `ConsistencyRule` is scoped narrowly to carry that one
   signal; it does not change the missing-data convention for
   `BodyWeightRule`, `BodyFatRule`, `MeasurementTrendRule`, or
   `PlateauRule`, all four of which still pass on missing data exactly
   as every other engine's rules do.

3. **"Consecutive flat weeks" (Table 54) is approximated as consecutive
   trailing *entries*, not calendar weeks, and this is a stated
   simplification, not a literal implementation.** `Progress` has no
   weekly cadence or lifecycle (ADR 0010) — nothing in the domain model
   guarantees entries arrive weekly, so `PlateauRule` reads its
   `minimum_consecutive_entries` trailing entries (default 4) and checks
   whether their range falls within a tolerance, regardless of the
   calendar gaps between them. A future increment that adds a real
   weekly-cadence concept to `Progress` (or a dedicated Statistical
   layer implementing true rolling averages, per Table 54's
   "Rolling-average preference") should revisit this rule to bucket by
   calendar week rather than by raw entry count.

4. **`MeasurementTrendRule` never fails — it only observes and reports,
   the same "always passes, no target to fail against" precedent
   `StrengthGoalRule` established in Goal Alignment (ADR 0016).** No
   `Goal` field in this codebase carries a target for waist, chest, hip,
   arm, thigh, calf, neck, lean body mass, or muscle mass — there is no
   domain-modeled "wrong direction" for any of these nine fields, so
   there is nothing for this rule to fail against. It surfaces
   meaningful changes (beyond a configurable noise threshold) as
   `RecommendationSeverity.ADVISORY` findings on an otherwise-passing
   result, exactly as `StrengthGoalRule` does for 1RM progress with no
   comparable `Goal` target.

## Consequences

Any future rule engine needing both a historical trend and a
goal-snapshot comparison at once should reuse this context shape —
`history: tuple[...]` plus a whole referenced snapshot — rather than
re-flattening fields into a single flat context, continuing the
precedent this phase establishes as the first to combine ADR 0016's and
ADR 0017's shapes.

`ConsistencyRule`'s fail-on-missing-data behavior is now the one
documented exception to the "missing data always passes" convention
across the entire domain layer. Any future rule considering the same
choice must find an equally explicit Bible instruction before deviating
from the default — this ADR's reasoning should not be read as loosening
the general convention, only as recording the one place it does not
apply and why.

`PlateauRule`'s entry-count approximation of "weeks" is a known gap
between the Bible's literal wording and this implementation. If a
future Progress Intelligence increment (the "separate, not-yet-built
context" the `Progress` aggregate's own module docstring already
anticipates) adds real statistical trend/forecast computation, this
rule's tolerance-window approach should be reconsidered against that
richer analysis rather than treated as the final word on plateau
detection.
