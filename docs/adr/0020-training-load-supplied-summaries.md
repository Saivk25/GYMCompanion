# ADR 0020: Training Load Rule Engine — application-layer-supplied summaries, literature-grounded acute/chronic windowing, and separation from Progressive Overload and Safety

- Status: accepted
- Date: 2026-07-30

## Context

Sprint 3, Phase 8 asked for `TrainingLoadRuleEngine`: evaluating
accumulated training load from immutable historical summaries. Five
rules were named — `AcuteLoadRule`, `ChronicLoadRule`, `LoadRatioRule`,
`MonotonyRule`, `StrainRule` — with a context described only as
containing "immutable historical summaries required for load
evaluation. The application layer is responsible for preparing the
summaries. No repositories. No services."

The Domain Model & Decision Engine Bible names no "Training Load"
bounded context (Section 3, Table 2's thirteen contexts) and no
`TrainingLoad` aggregate or entity (Section 5's catalog). Training load
appears only as an *input* to `RecoveryState`: "Recovery is a rolling
state derived from a window of Readiness snapshots plus training load"
(Section 2, Table 1; repeated in Section 4.8). Section 10.3's "Recovery
Rules" governs `RecoveryState` computation and deload triggering, but
neither it nor Table 50 (the Recovery Rules detail table already used
by `docs/adr/0018-safety-rule-engine-composition-and-authority.md`)
names acute:chronic workload ratio, training monotony, or strain by
those terms — these are established sports-science concepts (Foster et
al. 1998/2001; Gabbett 2016; Hulin/Blanch's "coupled" ACWR
convention), not Bible quotations.

Four design questions were specific to this phase:

1. **Every prior context-building phase (Progressive Overload, Safety,
   Progress Evaluation) either derives its own summaries from raw
   aggregate snapshots or defines small new value objects for data no
   aggregate carries. This phase's task text says the *application
   layer* prepares the summaries. Does this package still derive
   anything, or does it only consume?**
2. **With no Bible-specified thresholds or windowing convention, where
   should acute/chronic window sizes and numeric ceilings come from?**
3. **`LoadRatioRule`'s acute:chronic ratio overlaps conceptually with
   `app.domain.safety.rules.workload_rule.WorkloadRule` (a "too much,
   too soon" spike detector), and `AcuteLoadRule`/`ChronicLoadRule`
   overlap conceptually with Progressive Overload's `VolumeRule`
   (volume-trend detection) and `DeloadRule` (sustained near-peak
   volume detection). Is this three-way overlap a duplication bug?**
4. **`MonotonyRule` and `StrainRule` both need a standard deviation of
   daily load. Sample or population standard deviation?**

## Decision

1. **`TrainingLoadRuleContext` builds no summaries of its own — it only
   sorts and windows what the application layer already supplied.**
   Unlike `ProgressiveOverloadRuleContext.from_session_contexts()`
   (`app.domain.workout.rules.context`), which derives
   `WorkoutSessionSummary` from raw `WorkoutSessionContext` snapshots,
   this package declares no equivalent derivation method. A
   `TrainingLoadSummary` is one day's *already-computed* training load
   — a single opaque, non-negative scalar (`TrainingLoad`) the caller
   derived using whatever formula fits its own data (session-RPE x
   duration, `WorkoutSessionSummary.total_volume`, a wearable-reported
   metric, or anything else). This package does not know or care which
   formula produced the number, the same trust every context in this
   codebase places in its supplied fields taken one step further: here,
   the entire notion of "what counts as load" is deferred to the
   caller, not just individual field values. `TrainingLoadRuleContext.
   from_summaries()` still exists as the safer, sorting construction
   path (mirroring `ProgressiveOverloadRuleContext`'s and
   `ProgressEvaluationRuleContext`'s own `from_*()` methods), but it
   sorts only — it never computes a load value from anything else.

2. **Acute/chronic windowing (7-day acute, 28-day chronic, "coupled"
   normalization to a weekly-equivalent figure) and every numeric
   ceiling are this phase's own generic choices, explicitly grounded in
   general sports-science literature rather than the Product Bible,**
   the same category of grounding `docs/adr/0018-safety-rule-engine-
   composition-and-authority.md` already used for Safety's own
   `WorkloadRule` ("loosely related to the sports-science
   acute:chronic workload ratio concept... a stated simplification").
   `TrainingLoadRuleContext.trailing_window()` centralizes the
   window-selection logic in exactly one place — anchored to the
   *latest supplied entry's* date, never to `Clock`/today, the same "no
   wall-clock reads" discipline `ProgressiveOverloadRuleContext`
   established — so `AcuteLoadRule`, `ChronicLoadRule`, and
   `LoadRatioRule` all call the same method rather than each
   re-implementing date-range filtering. Every default threshold
   (`load_ceiling`, `monotony_ceiling`, `strain_ceiling`, the ratio's
   `low_ratio_threshold`/`high_ratio_threshold`) is a documented
   starting point for a real deployment to tune against its own
   chosen load formula's actual scale, not a universal constant — the
   same caveat `VolumeRule`'s `decline_threshold` and `CaloriesRule`'s
   range already carry.

3. **The three-way overlap between this engine, Safety's `WorkloadRule`,
   and Progressive Overload's `VolumeRule`/`DeloadRule` is deliberate,
   independent evaluation from three different angles, not duplication**
   — the same "independent rules, no shared state" posture ADR 0014
   established within one engine and ADR 0018 already extended across
   engine boundaries once. Concretely: Safety's `WorkloadRule` answers
   "is training safe *right now*" from a two-window average ratio,
   evaluation-only and CRITICAL-adjacent in intent; Progressive
   Overload's `VolumeRule`/`DeloadRule` answer "is *strength
   progression* trending correctly," reading `WorkoutSessionSummary`
   data this package never touches; this engine's `LoadRatioRule`
   answers "is the standard sports-science acute:chronic *load*
   relationship, specifically, in a risk range" using the literature's
   own coupled-window convention, independent of what formula produced
   the underlying `TrainingLoad` numbers. Three engines holding three
   independent opinions about related-but-distinct questions, each
   computed from data supplied in that engine's own context shape, is
   the intended shape of this codebase's rule-engine layer, not an
   accident to reconcile.

4. **`MonotonyRule` and `StrainRule` use population standard deviation
   (`statistics.pstdev`), not sample standard deviation, and this is a
   stated simplification.** Foster's original method treats the
   evaluated week as the entire population under consideration, not a
   sample drawn from a larger one — population `stdev` is the more
   literal reading and avoids Bessel's correction complicating the
   "identical load every day -> zero variance" edge case both rules
   special-case explicitly (an edge case that is exact with population
   `stdev`, since it never divides by `n - 1` and therefore never needs
   `n >= 2` guarding beyond what `minimum_entries` already requires).

## Consequences

Any future rule engine needing "already-computed values the
application layer prepares, not derived from any aggregate this
package can see" should reuse this shape — a context with only sorting
and windowing methods, no `from_*_contexts()` derivation method at all
— rather than assuming every future context must build its own
summaries the way Progressive Overload's does. This is now the second
distinct context-construction pattern in the codebase (alongside
Progressive Overload's derive-from-aggregate-snapshots pattern), and
future phases should pick deliberately between the two rather than
defaulting to one.

Every acute/chronic window size and numeric ceiling in this package is
explicitly flagged as literature-grounded, not Bible-mandated or
personalized — a future increment that adds real per-user calibration
(e.g. against a `Profile`'s training history, or the Statistical
layer's own rolling-average preference, Table 54) should treat these
defaults as replaceable starting points, not settled constants.

Because this package accepts training load as an opaque scalar with no
defined formula, it cannot itself guarantee that two different callers'
`TrainingLoad` values mean the same thing — a future application layer
combining this engine's output with `WorkoutSessionSummary`-based
Progressive Overload output, or with a wearable-reported metric, must
ensure whatever formula feeds `TrainingLoadSummary.load` stays
consistent for a given user across evaluations, since this package has
no way to detect or correct a formula change mid-history.
