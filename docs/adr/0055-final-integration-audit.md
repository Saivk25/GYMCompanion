# ADR 0055: Final end-to-end integration audit

- Status: accepted
- Date: 2026-08-11

## Context

After `docs/adr/0054-testing-and-release-readiness.md` concluded the
planned six-step production-integration roadmap
(`docs/adr/0042-production-integration-plan.md`), the user asked for one
last, read-only end-to-end architecture and codebase audit before
considering the project finished — explicitly not a new phase, and
explicitly not license for speculative refactoring. The instruction's
own exception was narrow: modify code only if a genuine correctness bug
is found; otherwise, list findings only. Eight things were named to
verify: stale references from any refactor/integration phase; repository
interface/implementation consistency; `main.dart` provider wiring; every
route resolving to a real screen with no orphans; no dead files/unused
exports/obsolete mock wiring; README/ADR/TECH_DEBT internal consistency;
ADRs 0042-0054 fully reflected in the codebase; and any blockers to a
future `flutter analyze`/`flutter test`/release build.

## Findings

1. **Repository interfaces vs. implementations.** Every `ApiXRepository`/
   `MockXRepository` across all six features (Today: 1 method, Train: 7,
   Fuel: 3, Progress: 2, Readiness: 2, Coach: 1) fully and consistently
   implements its own `XRepository` interface. No mismatch found.
2. **`main.dart` provider wiring.** All 9 `throw UnimplementedError`
   default providers (`sharedPreferencesProvider`, `authRepositoryProvider`,
   `tokenStorageProvider`, and one repository provider per feature) have a
   matching override in `ProviderScope.overrides`. No missing or orphaned
   override found.
3. **Route completeness.** All 29 registered `app_router.dart` paths
   resolve to 29 real, existing screen files. Every `context.push`/
   `context.go` call site across `lib/features` and `lib/shell` targets a
   registered path, including every interpolated dynamic segment (e.g.
   `/coach/signal/${signal.id}`, `/train/pre-session/${workout.workoutId}`).
   **One exception was found and is the one genuine correctness bug this
   audit fixed — see Decision below.**
4. **Dead files, unused exports, obsolete mock wiring.** A full import
   sweep (relative + `package:` imports, every `lib/` and `test/` file)
   found zero `lib/` files unreferenced by any other file, aside from
   `main.dart` itself (the app's own entrypoint, never imported by
   design). `main.dart` wires exactly one `Mock*Repository`
   (`MockCoachRepository`, via `coachRepositoryProvider`) — the disclosed,
   permanent exception `docs/adr/0051-coach-repository-integration.md`
   already established, since no backend `coach` concept exists to
   integrate against. Every other feature's `Mock*Repository` is
   referenced only from `test/`, exactly as `docs/adr/0046` through
   `0050` each intended. No dead file, no unused export, no obsolete mock
   wiring found.
5. **README/ADR/TECH_DEBT consistency.** `docs/TECH_DEBT.md`'s 14 items
   (TD-0001 through TD-0014) were re-read in full: each still accurately
   describes a real, current, deliberately-deferred trade-off with a
   concrete trigger condition, and none contradicts the current code
   state. `apps/mobile/README.md`'s Status section was re-read in full
   against the code it describes (Today/Train/Fuel/Progress/Readiness/
   Coach sections, the Step 1-6 production-integration summary) and found
   accurate, with one line (`TodaySessionSummary`'s field list) updated as
   part of this audit's own fix — see Decision.
6. **ADRs 0042-0054 reflected in the codebase.** A sweep of every
   `docs/adr/00(4[2-9]|5[0-4])` reference across `lib/` found 43 files
   with a live doc-comment citation to one of these ADRs, spanning every
   layer this roadmap touched (`core/network`, `core/cache`,
   `core/mapping`, all six features' infrastructure/application/domain/
   presentation layers, `shell/`, `app.dart`, `main.dart`). Combined with
   findings 1-3 above (which independently verify the roadmap's
   structural claims — real repositories wired, real routes, real
   providers), the roadmap is substantively and traceably reflected in
   the code, not just documented in prose.
7. **Blockers to `flutter analyze`/`flutter test`/a release build.**
   Unchanged from every prior phase (`docs/adr/0002`): no Flutter SDK is
   available in this environment, and no `android/`/`ios/` platform
   folders exist in `apps/mobile/` (confirmed directly — `ls` finds
   neither). Nothing else found in this audit blocks a first real run —
   no unresolved import, no unclosed brace, no obviously-malformed
   construction site across the files this audit touched or read in
   full. The first real verification these files (and every file this
   roadmap produced) get remains `flutter pub get` / `flutter analyze` /
   `flutter test` on a machine with the SDK installed.

## Decision

**One genuine correctness bug was found and fixed**, per this audit's
own stated exception. `TodayScreen`'s "Start session" action
(`lib/features/today/presentation/today_screen.dart`) pushed a
hardcoded literal, `context.push('/train/pre-session/workout-today')`.
`'workout-today'` was always `MockTrainRepository`'s own fixture id for
today's workout, disclosed as a temporary coupling in the surrounding
comment at the time it was written — but the promised follow-up
("a real repository pass will add a real `workoutId` to
`TodaySessionSummary` and this literal goes away") never happened even
though the real repository pass (`docs/adr/0046-today-repository-
integration.md`) has been built and permanently wired since Step 3.
`ApiTodayRepository._buildViewState` already had the real workout's real
id available (`WorkoutDto.workoutId`) but never passed it into the
`TodaySessionSummary` it constructs. Since `ApiTrainRepository.fetchWorkout`
makes a real `GET /api/v1/workouts/{workoutId}` call, navigating with the
literal `'workout-today'` id would issue a real request with a
nonexistent id against the real backend — the app's primary landing-
screen call to action, broken against production.

Fixed with this project's established additive-parameter pattern (the
same shape as `LocalCache.write`'s optional `cachedAt`):

- `TodaySessionSummary` (`lib/features/today/domain/today_models.dart`)
  gained a required `workoutId` field.
- `ApiTodayRepository._buildViewState` now passes
  `workoutId: todaysWorkout.workoutId` — the real backend id.
- `MockTodayRepository` now passes `workoutId: 'workout-today'`,
  matching `MockTrainRepository`'s own existing fixture id, so a
  mock-based tap-through from Today into Train's Pre-session screen
  still resolves correctly.
- `TodayScreen.onStartSession` now pushes
  `'/train/pre-session/${state.session!.workoutId}'` instead of the
  literal; the stale comment explaining the old placeholder was rewritten
  to describe the current, real state instead of still promising a fix
  that had already should have landed.
- `test/features/today/today_screen_test.dart`'s `_baseState()` fixture
  updated to supply `workoutId: 'workout-today'`.

The `state.session!` null-check this fix relies on was verified safe,
not assumed: `ApiTodayRepository._sessionStatusFor` only returns
`.ready`/`.completed` when the same `WorkoutDto?` that also produces
`session` is non-null, and `MockTodayRepository` always pairs
`SessionCardStatus.ready` with a non-null `session` literal — so
`SessionCardStatus.ready` and a null `session` cannot co-occur in either
repository today. This also matches the file's own existing style
(`summary.goal!`, `summary.notes!`, `session!.name` are already used
under the same invariant elsewhere in `session_card.dart`), so this fix
introduces no new risk pattern beyond what the file already relies on.

No other issue found during this audit required a code change. Findings
1-2 and 4-7 above found the codebase already consistent; no stale
reference, dead file, unused export, obsolete mock wiring, or
documentation contradiction was found anywhere else.

## Consequences

The implementation is internally consistent: every repository interface
matches its implementation, every provider is wired, every route
resolves, no dead code or stale mock wiring remains, and the
documentation (README, 55 ADRs, 14 TECH_DEBT items) accurately reflects
the current code. The one genuine bug this audit found was in the class
of defect this kind of end-to-end audit exists to catch — a disclosed,
temporary placeholder whose own promised follow-up silently never
happened across several later phases — and it is now closed. What
remains before this app is release-executable is unchanged from ADR
0054's own assessment: real-device validation, `flutter analyze`/
`flutter test`/a real build once a Flutter SDK is available, platform
folder generation, and release engineering (app icon, splash screen,
store metadata, a real TalkBack/VoiceOver pass) — none of which is a
gap in this roadmap's own planning or a defect this sandbox could have
caught earlier.
