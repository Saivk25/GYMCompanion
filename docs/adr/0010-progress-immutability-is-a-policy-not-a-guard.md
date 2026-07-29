# ADR 0010: Progress's "immutable after recording" rule is a documented policy, not a domain-layer guard

- Status: accepted
- Date: 2026-07-29

## Context

Sprint 2, Step 6 asked for a `Progress` aggregate — the user's canonical
fitness history (body weight, body composition, tape measurements) —
with an explicit rule: "Progress records become immutable after recording
(future corrections should create new records rather than mutate
history)." The same task also names four events, three of which are
mutations: `ProgressRecorded`, `MeasurementsUpdated`,
`BodyCompositionUpdated`, `ProgressNotesUpdated`. No `ProgressStatus`
(or equivalent) enum was requested, unlike every prior aggregate with a
mutation-blocking rule (`User.AccountStatus`, `Workout.WorkoutStatus`,
`Exercise.ExerciseStatus`, `WorkoutSession.SessionStatus`).

This creates a real tension a design decision had to resolve: the task
names update methods/events for this aggregate, but also states records
become immutable — with no state field given to gate those updates on.
Three prior ADRs (0005, 0006, 0008) already established the pattern of
naming this kind of ambiguity explicitly rather than silently picking one
reading; this is the same class of decision.

The Domain Model & Decision Engine Bible's closest concept, `Measurement`
(Section 4.10, Table 13), is described as "a sibling append-only log on the
same review cadence" as `PhotoCheckin` — consistent with the task's
immutability rule, but the Bible doesn't specify a mechanism either; "
append-only" is a description of the intended usage pattern, not a
enforced state machine in the source material.

## Decision

**"Immutable after recording" is implemented as documented policy for
callers of this aggregate, not as a domain-layer guard that rejects calls
to `update_body_composition()`/`update_measurements()`/`update_notes()`.**
These three methods are real, unconditionally-callable mutations — the
task's own event list requires them to exist and fire. `Progress` has no
status enum and no lifecycle; a single check-in is a fact captured at a
point in time, not a multi-step workflow like a `Workout` or
`WorkoutSession`, so there is no natural state to gate mutation on without
inventing one the task never asked for.

The intended, correct usage is:

- The three update methods exist for amending a record still being
  actively assembled — the ordinary case where a user weighs in, and a
  smart-scale sync or a tape measurement arrives moments later for the
  same check-in, before that check-in is considered "closed."
- Once a `Progress` record is treated as closed/historical by the
  application layer, correcting it means constructing and persisting a
  **new** `Progress` record via `record()`, not calling an `update_*`
  method on the old one. This is exactly the `ExercisePerformance`/
  `ExerciseSet` precedent inverted: ADR 0009 kept mutation *inside* one
  aggregate instance because a session and its logged sets share one
  consistency boundary; here, each `Progress` record is itself the unit of
  history, so a correction is a new instance, not a new state inside the
  same one.
- Nothing in this domain layer can currently tell these two situations
  apart — there's no timestamp-based or explicit "close" concept recorded
  anywhere on `Progress`. That is a genuine, acknowledged gap, not a
  contradiction papered over: the alternative (inventing a `ProgressStatus`
  with, say, `Draft`/`Finalized` states) is real, additional scope this
  task didn't request, and would need product input on what "finalized"
  actually means for a body-measurement check-in (immediately? end of day?
  after N hours?) that isn't answered anywhere in the source documents.

## Consequences

Any future increment that wants to *mechanically* enforce "never mutate a
closed record" has two additive options, neither breaking today's shape:
add an explicit `finalize()`/lock concept to `Progress` itself (a new,
optional state), or enforce the rule entirely at the application/service
layer (the layer that already decides whether to `repository.get()` an
existing record to amend it or construct a new one via `record()` — this
increment's domain layer exposes both operations correctly either way).

`ProgressRepository` stays shaped like every other aggregate's repository
(`get`/`add`/`remove`, no `update`) — this is not itself an enforcement
mechanism (every other aggregate mutates in place and is expected to be
re-persisted the same way), so it must not be read as "proof" the
immutability rule is mechanically guaranteed.

Progress Intelligence (Trend/PlateauEvent/Forecast, Bible Section 4.9/9.3,
not built yet) reading a series of `Progress` records for a user should
treat `MeasurementsUpdated`/`BodyCompositionUpdated`/`ProgressNotesUpdated`
events on an old record as a signal worth surfacing (a correction happened
after the fact) rather than assuming they only ever occur within moments
of the record's `ProgressRecorded` event — the domain layer does not
prevent the latter from happening, even though it shouldn't, by policy.
