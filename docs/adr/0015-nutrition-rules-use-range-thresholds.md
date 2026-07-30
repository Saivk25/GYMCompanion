# ADR 0015: Nutrition rules validate a `[minimum, maximum]` range per field, not a single-sided threshold

- Status: accepted
- Date: 2026-07-30

## Context

Sprint 3, Phase 3 asked for six Nutrition rules — `CaloriesRule`,
`ProteinRule`, `CarbohydratesRule`, `FatRule`, `FiberRule`,
`HydrationRule` — each validating one `NutritionRuleContext` field
"against configurable minimum and maximum thresholds"
(`CaloriesRule`'s own spec) or "configurable thresholds" (the other
five). The task asked this ADR to document the independent-rule
composition strategy only "if it introduces any Nutrition-specific
architectural decision beyond the shared Rule Engine foundation." The
composition strategy itself — many small, single-concern `Rule`
subclasses composed by one thin `XyzRuleEngine` — is not a new decision
here; ADR 0014 (Sprint 3, Phase 2) already established that as this
codebase's expected shape for every future rule engine, and this package
follows it without modification.

One thing genuinely is new: every Readiness rule (ADR 0014) checks its
field against a single threshold — a floor (`EnergyRule`'s minimum) or a
ceiling (`StressRule`'s maximum), never both on the same field.
`RecoveryRule` was the one exception, but even it evaluates two
*separate* fields (resting heart rate, HRV) with one threshold each, not
one field against two bounds. Every Nutrition rule in this phase, by
contrast, validates one field against a `[minimum, maximum]` range —
both bounds, on the same field, in the same rule.

## Decision

**Every Nutrition rule takes both a `minimum_*` and `maximum_*`
constructor parameter and fails when the observed value falls outside
`[minimum, maximum]`**, not just below a floor or above a ceiling. This
is a direct, literal reading of `CaloriesRule`'s own task spec ("minimum
and maximum thresholds") applied uniformly to the other five for
consistency — a caller should not have to remember which nutrition rules
have one bound and which have two.

This is a natural fit for what these fields actually are: nutrition
totals (calories, protein, carbohydrates, fat, fiber, water) are
naturally two-sided sanity checks — too little intake is a real concern
(under-fueling, dehydration), but so is an implausibly large logged
number, which is far more often a *data-entry error* (a duplicated meal
entry, a decimal-point slip on a barcode-free manual log) than a genuine
nutritional event. Readiness's subjective 1-10 ratings and physiological
metrics don't share that "either bound might really just mean a typo"
character, which is why single-sided thresholds were the right shape
there and two-sided ranges are the right shape here — the two ADRs are
not in tension; each reflects what its own domain's numbers actually look
like.

## Consequences

Every Nutrition rule's failing `RuleResult.explanation` distinguishes
which bound was violated ("below the minimum" vs. "above the maximum"),
and each rule attaches a bound-appropriate `Recommendation` (e.g.
`CaloriesRule` suggests checking for missing entries on a low reading,
duplicate entries on a high one) — a caller cannot tell from `passed`
alone which direction the problem is in, but always can from
`explanation` or by inspecting which rule triggered.

The upper bounds this phase ships (4000 kcal, 250 g protein, 400 g
carbohydrates, 150 g fat, 70 g fiber, 6000 ml water) are generic,
single-day sanity ceilings, not "this is unhealthy" judgments — they
exist mainly to catch logging errors, the same reasoning
`fiber_rule.py` and `hydration_rule.py` state explicitly in their own
docstrings. A future increment building real personalized targets
(`MacroFactor`-equivalent adaptive calculation, explicitly out of scope
for this phase) should not read these defaults as intended targets to
tighten — they are a different, narrower kind of check and should
continue to coexist with, not be replaced by, whatever that increment
adds.
