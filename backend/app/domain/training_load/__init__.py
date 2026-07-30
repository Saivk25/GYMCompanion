"""The Training Load supporting package.

Unlike every other top-level package under `app.domain`, this one maps
to no bounded context the Domain Model & Decision Engine Bible names
directly (Section 3, Table 2 lists thirteen bounded contexts; "Training
Load" is not one of them). The Bible instead treats training load as an
*input* to `RecoveryState`: "Recovery is a rolling state derived from a
window of Readiness snapshots plus training load" (Section 2, Table 1;
repeated in Section 4.8's `RecoveryState` purpose statement). No
`TrainingLoad` aggregate or entity exists anywhere in the Bible's
catalog (Section 5) to build here.

`app.domain.training_load.rules` is the only thing this package holds:
Sprint 3, Phase 8's Training Load Rule Engine, which evaluates
accumulated training load from historical summaries the *application
layer* supplies — this package builds no summaries of its own, unlike
`app.domain.workout.rules`'s `WorkoutSessionSummary`. See
`app.domain.training_load.rules`'s own docstring and
`docs/adr/0020-training-load-supplied-summaries.md` for why, and for
how this engine stays a distinct, independent opinion from Progressive
Overload's and Safety's own load-adjacent rules rather than a
duplicate of either.
"""
