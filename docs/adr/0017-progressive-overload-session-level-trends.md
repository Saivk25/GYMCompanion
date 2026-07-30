# ADR 0017: Progressive Overload Rule Engine — pre-computed session summaries, peak-vs-average trend rules, and a distinct deload signal

- Status: accepted
- Date: 2026-07-30

## Context

Sprint 3, Phase 5 asked for `ProgressiveOverloadRuleEngine`: the first
rule engine that evaluates a *history* of immutable snapshots —
`WorkoutSessionContext` values spanning many sessions — rather than one
aggregate's (or two aggregates') state at a single point in time. Five
rules were named: `VolumeRule`, `IntensityRule`, `FrequencyRule`,
`ProgressionRule`, `DeloadRule`. The context "may include:
`WorkoutSessionContext`, `ExercisePerformance` snapshots, historical
summaries already supplied by the application layer... do not query
repositories, do not access services."

Four design questions were specific to this phase, not already answered
by ADR 0013 (Rule Engine foundation), ADR 0014 (independent-rule
composition), ADR 0015 (range thresholds), or ADR 0016 (whole-snapshot
contexts, explicit reference dates):

1. **How should five rules avoid recomputing the same volume/load
   arithmetic from raw `ExerciseSet` tuples five times over?** Every
   prior context's rules read already-typed fields directly
   (`context.calories`, `context.goal.target_weight`); nothing prior
   needed to *derive* a number from nested collections before a
   threshold check could even happen.
2. **What does "training volume" and "intensity" mean without a 1RM or
   per-exercise normalization this phase does not build?** The Domain
   Model & Decision Engine Bible names "Progressive overload engine:
   deterministic rep/load/set progression rules" (Product Bible) and
   tracks "Volume per muscle group... RIR trend, session duration"
   (Product Bible Table 18) without specifying the exact computation.
3. **How does a rule reason about "trend" from an ordered list, with no
   `reference_date` (nothing here asks "how does this compare to
   today")?**
4. **Is this engine's `DeloadRule` the same "deload trigger" the Bible
   names under Recovery Rules (Section 10.3)?**

## Decision

1. **`ProgressiveOverloadRuleContext` holds pre-computed
   `WorkoutSessionSummary` values, not raw `WorkoutSessionContext`
   snapshots.** `WorkoutSessionSummary.from_session_context()` computes
   `total_volume` (sum of weight x reps across every logged set) and
   `average_load` (mean set weight) once per session, so every rule
   reads the same two numbers rather than five independent
   re-derivations. This is exactly the "historical summaries already
   supplied by the application layer" option this phase's own task
   named — the summarizing lives in this package (still
   framework-independent, still no repository/service access), not in a
   hypothetical application-layer module this phase does not build.
   `ProgressiveOverloadRuleContext.from_session_contexts()` additionally
   sorts by `session_date` and filters to `Completed` sessions only —
   `Planned`/`Active` sessions have not finished, and `Abandoned`
   sessions may hold only a partial record, either way not reliable
   trend evidence.

2. **Volume and intensity are computed at whole-session granularity,
   with every logged `ExerciseSet` counted regardless of its own
   `completed` flag.** Two stated simplifications, not silently assumed:
   `ExerciseSet.completed` is a UI-level confirmation step
   (`ExercisePerformance.complete_set()`), not "was this actually
   performed" — `weight`/`reps`/`rpe` are already supplied together at
   logging time, which is what "record what just happened" means (see
   `exercise_set.py`'s own module docstring) — so the owning
   `WorkoutSession.status` being `Completed` is the reliability gate,
   not the per-set flag. Separately, combining every exercise in a
   session into one `total_volume`/`average_load` mixes genuinely
   different movements' loads (a 15 kg curl and a 100 kg squat both
   count toward the same session's "average load"), and blends
   zero-load bodyweight sets in with weighted ones. A future increment
   computing genuine per-exercise progression (e.g. against
   `Exercise`-scoped history, or a %1RM-normalized intensity measure)
   would need to replace this whole-session summary, not just retune
   its thresholds — documented in `WorkoutSessionSummary`'s own
   docstring, the same "name limitations explicitly" discipline ADR
   0016 established for `BodyWeightRule`'s unit mismatch.

3. **No `reference_date` field, unlike `GoalAlignmentRuleContext`.**
   Every judgment in this package is relative — "how does the later half
   of this history compare to the earlier half," "what's the rate across
   this span," "did any session in the last N break a historical peak" —
   never "how does this compare to today." `FrequencyRule` computes its
   rate purely from the span between the earliest and latest session
   *in the supplied history*, not from a wall clock. This keeps every
   rule a pure function of `context` (ADR 0013's contract) with no clock
   dependency to inject at all, a simpler case than ADR 0016's, not a
   contradiction of it. `VolumeRule`, `IntensityRule`, and
   `ProgressionRule` share an identical earlier-half/later-half split
   (a private `_earlier_and_later_halves()` helper, duplicated verbatim
   in each of the three files rather than factored into a shared
   module) — the same "small duplication over coupling between
   independent rules" posture ADR 0014 established for Readiness's
   shared guard pattern, continued here for a computational helper
   instead of a guard clause.

4. **`VolumeRule`/`IntensityRule` detect *decline* (a trend going the
   wrong direction); `ProgressionRule` detects *stagnation* (no new
   peak at all).** These are deliberately different questions: a session
   history can show a perfectly flat average (passing both `VolumeRule`
   and `IntensityRule`, since flat is not declining) while still
   plateauing at the same ceiling indefinitely — exactly the gap
   "deterministic rep/load/set progression rules" (Product Bible) is
   meant to catch. `ProgressionRule` compares *peak* `total_volume` and
   *peak* `average_load` between the earlier and later halves, not
   averages, because a peak is what "reached a new high" actually means;
   an average can rise even while the peak stays flat, and vice versa.

5. **`DeloadRule` here is a distinct, narrower signal from the Bible's
   Recovery-Rules deload trigger (Section 10.3), not an implementation
   of it.** The Bible's deload trigger reads `RecoveryState` and
   `ReadinessCheckIn` data — both `RecoveryState` and the eventual
   Recovery Rule Engine are explicitly out of scope for this phase.
   This `DeloadRule` can only see that training volume has stayed near
   its historical peak for a trailing window with no lighter session in
   between (a Workout-Rules-scoped, Section 10.1 "volume" concern) — it
   has no visibility into whether the user is actually fatigued or
   under-recovered. A future Recovery Rule Engine's deload trigger and
   this rule are two independent, non-overlapping signals that may both
   exist side by side; this rule does not pre-empt or subsume that
   future work.

## Consequences

Any future rule engine that evaluates a *history* of snapshots (nothing
else in this codebase does yet) should default to this same "pre-compute
one summary value object per snapshot via a `from_*()` factory, then run
every rule against the summaries" shape rather than having each rule
re-derive its own numbers from raw nested collections — the summary
becomes the one place a real simplification (like the whole-session,
mixed-exercise granularity documented here) gets stated once instead of
assumed silently in five places.

Because `WorkoutSessionSummary`'s volume/intensity numbers are
whole-session and mixed-exercise, any consumer of this engine (a future
application-layer module, not built here) should not present
`VolumeRule`/`IntensityRule`/`ProgressionRule` findings as "this specific
exercise isn't progressing" — only as a whole-program-level signal. A
real per-exercise progressive overload engine remains a genuinely new,
larger increment, not a threshold tweak to this one.

`DeloadRule`'s workout-volume-only heuristic should not be presented to
users as an authoritative recovery/deload verdict once a real Recovery
Rule Engine exists — at that point, an application-layer consumer
combining both engines' outputs (not built here) would need to decide how
the two signals relate, which this phase does not attempt to resolve.
