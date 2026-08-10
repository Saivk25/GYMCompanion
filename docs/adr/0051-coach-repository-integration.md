# ADR 0051: Coach repository integration — Step 3, feature 6 (confirmed complete, no HTTP repository required)

- Status: accepted
- Date: 2026-08-10

## Context

Step 3 of `docs/adr/0042-production-integration-plan.md`'s sixth and
final feature. Every prior phase (Today, Readiness, Train, Fuel,
Progress) followed the same shape: replace a `MockXRepository` with a
real `ApiXRepository` built on the shared `ApiClient`/mapping
convention (`docs/adr/0045`). Before repeating that shape here,
research re-verified whether it still applies to Coach, since ADR 0041
already found — before any of Today/Readiness/Train/Fuel/Progress had
been switched to real backends — that Coach has no backend concept to
call at all.

Re-verification performed this phase, not assumed from ADR 0041 alone:

1. **A fresh recursive search for `coach` across the entire backend**
   (`grep -ril coach backend/app/`) returns only three false-positive
   matches — the string `COACH` inside an unrelated auth-role code
   comment, and two unrelated uses of the English word "coaching" in a
   workout-session value-object comment. `ls backend/app/api/routes/v1/`
   lists exactly five route modules (`goal.py`, `nutrition.py`,
   `progress.py`, `readiness.py`, `workout.py`) — no `coach.py`, no
   aggregation or recommendation-history route anywhere. ADR 0041's
   finding #1 ("no `coach` concept anywhere in the backend") still
   holds, unchanged, after five more phases of backend research on this
   same codebase.
2. **`CoachSignalLog` already sources real, not mock, warnings.**
   `ReadinessHomeController.submitCheckIn`, `FuelHomeController
   .logMeal`, and `ActiveSessionController.completeSession` each still
   call `ref.read(coachSignalLogProvider.notifier).add(module, result
   .warnings)` (confirmed by re-reading all three call sites) — a line
   ADR 0041 added when Readiness/Fuel/Train were still mock-backed.
   Because that line reads `result.warnings` off whatever repository
   the module's own provider currently resolves to, and
   `docs/adr/0047`/`0049`/`0048` already replaced those three
   repositories' real HTTP calls without touching this line, `Coach
   SignalLog` has been populated by genuinely real,
   backend-computed advisory strings — not illustrative mock text —
   since the moment Readiness/Fuel/Train each finished their own Step 3
   phase. This phase changed no code in any of those three controllers;
   it only re-confirms and formally records that the swap already
   completed the work Coach itself would otherwise need.
3. **No new rule engine, endpoint, or aggregation capability has
   appeared.** `SafetyRuleEngine` is still unreferenced by any handler
   (`grep -rl SafetyRuleEngine backend/app/application backend/app/api`
   returns zero hits, re-run this phase). No Flutter feature module for
   Goal exists (`grep` for "goal" in `lib/features/` matches only
   unrelated session-goal text in Today/Train, not a Goal feature
   folder) — both exactly as ADR 0041 found.

## Decision

**No `ApiCoachRepository` is built, and none is needed.** `Coach
Repository`'s own doc comment already states this precisely: it "is not
a stand-in for a future HTTP client." `MockCoachRepository` already
*is* Coach's real, production implementation — it reads
`CoachSignalLog`, a session-scoped in-memory store, which by the
argument in point 2 above already contains only real backend-sourced
data once Readiness/Fuel/Train are each on their own real repositories.
Introducing a network call here would not make Coach "more real" — it
would either (a) fabricate an endpoint the backend does not have, or
(b) require rebuilding the backend's own missing aggregation
capability, which is out of scope for a Flutter-side integration phase
and was already explicitly rejected as a path in ADR 0041 Decision 6.

**No domain model, repository interface, or presentation contract
changed.** `CoachRepository.fetchRecentSignals()`,
`CoachSignal`/`CoachModule`/`CoachSeverity`, `CoachSignalLog`, and every
Coach screen are unchanged by this phase — there was no mismatch to
stop and ask about, because there was no gap between what the interface
promises and what the backend can deliver that ADR 0041 had not already
resolved.

**`main.dart`'s composition root needed no change.**
`coachRepositoryProvider.overrideWith((ref) => MockCoachRepository(()
=> ref.read(coachSignalLogProvider)))` was already correct before this
phase and remains so — it was never a placeholder standing in for a
future `ApiCoachRepository.overrideWith(...)` the way the other five
providers' mock overrides were.

## Consequences

Step 3 of `docs/adr/0042-production-integration-plan.md` is now
complete for all six features. Five features
(Today/Readiness/Train/Fuel/Progress) ended with a new `ApiXRepository`
class; Coach ends with a formal confirmation, recorded here, that its
existing `MockCoachRepository` already satisfies the same "real,
non-fabricated data" bar the other five needed a network client to
reach — because Coach's real data source was never an HTTP endpoint to
begin with.

No files changed in `apps/mobile/lib/` or `apps/mobile/test/` as a
result of this phase — the only artifacts are this ADR and the
corresponding README/`main.dart` doc-comment updates recording Step 3's
completion.

If a future backend phase ever adds a real aggregation, persistence, or
history endpoint for advisory output — the one scenario ADR 0041
Decision 6 already anticipated for Weekly Review/Coaching History —
that would be new backend capability requiring its own research and its
own ADR, not a gap this phase left open.
