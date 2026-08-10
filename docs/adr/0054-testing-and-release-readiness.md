# ADR 0054: Testing and release readiness — Step 6 of production integration

- Status: accepted
- Date: 2026-08-11

## Context

Step 6 of `docs/adr/0042-production-integration-plan.md`, the concluding
phase of the production-integration roadmap. Scoped by the user as
validation and release preparation — not new features or architectural
redesign: expand/review the test suite where appropriate, audit for
coverage gaps rather than write unnecessary tests, verify ADR 0042's own
release checklist against current state, sweep for dead code/stale docs/
outdated comments, and fix only low-risk issues (stopping to ask before
anything requiring a design decision).

## Testing findings and coverage summary

**Repository tests exist for all five real repositories** (Today,
Readiness, Train, Fuel, Progress) plus the shared cache layer
(`test/core/cache/`) — the single category ADR 0042 Part 6 named as not
existing at all before Phase 2 began. This gap is fully closed.

**Screen coverage was re-checked against ADR 0042 Part 1's own uneven-
coverage finding, using actual navigation behavior, not just route-string
greps** (a route is reached by tapping through the UI in every test in
this suite, never by asserting on a literal path string, so "does a
screen have a test" has to be checked by tracing what a flow test
actually taps into). Result: every screen in Train, Fuel, Progress, and
Readiness is genuinely exercised, several only incidentally inside a
flow test's own multi-step navigation (e.g. `ExerciseDetailScreen` via
Active Workout's "Cues" button, `PhotoComparisonScreen` via Progress's
Transformation section) — legitimate coverage, not a gap, even though a
plain file-count ratio would suggest otherwise. **One genuine gap was
found and closed:** `CoachSignalDetailScreen` had zero coverage anywhere
— no test ever tapped a `CoachSignalTile` to open it. Fixed by adding a
test to `coach_home_screen_test.dart` (see Fixes below).

**Navigation-preservation coverage is real but distributed, not a
dedicated suite.** ADR 0042 Part 6 item 3 asked for "a real test suite
exercising every `parentNavigatorKey` drill-in route... confirming
`context.push`/`pop` round-trips correctly restore the originating tab's
state." This exists, but as an assertion embedded in each feature's own
flow test rather than one dedicated file — e.g.
`train_screens_test.dart`'s "opening a past session from History shows
'Return to history'... Back on Train Home, still showing the History
tab" and `checkin_flow_test.dart`'s equivalent for Readiness. This
substantively satisfies the concern (a regression in tab-state
preservation would fail one of these existing tests) without a
redundant, separately-maintained navigation-only suite duplicating the
same pushes/pops these flow tests already perform. Not changed — adding
a parallel suite would be new test surface with no new protection.

**Accessibility: the automatable subset from ADR 0042 Part 6 item 4 had
never been added — now it has, for two representative screens.**
`flutter_test`'s own `meetsGuideline(androidTapTargetGuideline)`/
`meetsGuideline(textContrastGuideline)` matchers require only the widget-
test harness, not a real device — the one part of Part 5's accessibility
findings that doesn't need TalkBack/VoiceOver. Zero uses of
`meetsGuideline` existed anywhere in the suite before this phase.
Added: `test/accessibility/guideline_test.dart`, checking Today (the
landing screen) and Coach Home (badges, filter chips, and tiles
together — the specific "components that pass individually, now laid
out next to each other" combination ADR 0042 Part 5 flagged as
unverified). This is a representative sample proving the check exists
and is wired correctly, not a claim that every screen has been swept —
recorded as `docs/TECH_DEBT.md` TD-0014 with a trigger for widening it.

**Golden tests remain not built — a real, disclosed, environment-forced
gap, not an oversight.** `matchesGoldenFile` requires a Flutter SDK to
render and compare (or generate, via `--update-goldens`) an actual PNG
baseline — impossible in this sandbox (`docs/adr/0002`, unchanged).
Writing golden test *files* with no way to generate their baseline
images would produce tests that fail on their very first real run, which
is worse than not writing them: a red test with no signal in it. ADR
0042 Part 6 item 2 already anticipated golden tests needing a real SDK;
this phase confirms that constraint still holds and does not work around
it with an inert file.

**TD-0004's date-formatting consolidation remains open, deliberately not
folded into this phase.** Its own trigger condition ("before golden
tests are written") did not fire, since golden tests were not written
this phase for the reason above. It is a genuine, multi-file (7+
presentation files), low-risk-but-not-trivial refactor — the same shape
this project's own backend precedent (TD-0001) treated as its own
standalone, dedicated unit of work rather than a drive-by inside a
broader phase. Left open rather than rushed through a testing-focused
phase; see Remaining known limitations.

## Release-readiness assessment

Verified against `docs/adr/0042-production-integration-plan.md`'s own
9-item release checklist, in order:

1. **Generate platform folders + run the suite on a real
   device/simulator.** Not done — `android`/`ios` folders still do not
   exist; nothing in this Flutter codebase has ever actually executed
   (`docs/adr/0002`'s standing constraint, unchanged through every one of
   the six phases this roadmap comprised).
2. **Fix TD-0003 + TD-0004.** TD-0003 partially resolved (icon tokens
   fixed; Settings fixed with real logout; Search/Notifications remain
   disclosed no-ops awaiting a real destination decision — unchanged
   since Step 2). TD-0004 open (see above).
3. **Phase 2 (API client, auth, real repositories).** Done — Steps 1-3 of
   this roadmap.
4. **Phase 3's supportable offline subset.** Done — Step 4
   (`docs/adr/0052`).
5. **Real DevTools performance pass.** Not done — Step 5 was static
   analysis only, by necessity and by explicit instruction
   (`docs/adr/0053`).
6. **Real TalkBack/VoiceOver pass.** Not done — same constraint; Step 5's
   own findings are the static-analysis substitute, not equivalent to a
   real screen-reader pass.
7. **Testing plan.** Substantially done: repository tests (done), widget-
   test gap-filling (one real gap found and closed this phase), the
   automatable accessibility subset (done this phase), navigation
   coverage (substantively satisfied, distributed rather than dedicated).
   Golden tests and integration tests against a real backend remain
   undone, both for the same real-SDK/real-backend-instance reasons ADR
   0042 itself anticipated.
8. **`GoRouter.errorBuilder`, app icon, splash screen, store metadata.**
   Not done. `errorBuilder` specifically was rechecked this phase
   (`grep -rn errorBuilder lib/` — zero matches) — still Flutter's
   default, unbranded error widget for an unmatched route. App icon/
   splash/store metadata remain entirely unstarted, same as ADR 0042's
   own Part 7 finding — these depend on platform folders existing at
   all (item 1).
9. **Full regression pass, then submission.** Not reachable — blocked on
   1, 5, 6, and 8 above, all of which require a real Flutter SDK/device
   this environment does not have, or product decisions (app icon design,
   Search/Notifications' real destinations) outside this phase's own
   "validation and release preparation, not new features" scope.

**Overall: this app is architecturally release-ready — every backend
integration, offline behavior, and structural audit this roadmap
planned is complete and internally consistent — but is not yet
release-executable.** The remaining checklist items are not missing
engineering; they are the parts of the checklist that always required a
real device and a real store submission process, explicitly flagged as
such from the moment ADR 0042 was written.

## Fixes applied

1. **`CoachSignalDetailScreen` test coverage gap closed** — one new
   `testWidgets` in `test/features/coach/coach_home_screen_test.dart`,
   tapping a real signal tile and asserting the detail screen's message,
   module, and "where this came from" disclosure render correctly.
2. **Automatable accessibility guideline tests added** —
   `test/accessibility/guideline_test.dart` (new file), covering Today
   and Coach Home against `androidTapTargetGuideline`/
   `textContrastGuideline`.

No other fix was applied. Every other finding above either requires a
real Flutter SDK/device this environment cannot provide (golden tests,
DevTools, TalkBack/VoiceOver, platform folders, store submission) or is
a genuine, multi-file refactor better scoped as its own dedicated unit
of work (TD-0004) than folded into a testing-and-validation phase —
consistent with this phase's own "fix only low-risk issues... stop and
ask before anything requiring a design decision" instruction. Nothing
found during the dead-code/stale-documentation sweep required a fix:
`main.dart`'s composition-root doc comment, every repository's own doc
comments, and `pubspec.yaml`'s dependency comments were all re-read in
full and found to accurately describe the current, real state of the
code — no leftover "not yet wired"/"will be replaced" language, no
`TODO`/`FIXME` markers, no unused files.

## Remaining known limitations

- TD-0004 (date-formatting consolidation) — open, no change in status.
- TD-0009 through TD-0013 (Step 4/5 findings — cache SWR/pull-to-refresh
  trade-off, Readiness Timeline's eager list, missing `.autoDispose` on
  Train's per-workout/session providers, `LoggedSetRow`'s touch target,
  missing focus-chaining on three forms) — all still open, unchanged.
- New: TD-0014 (accessibility guideline tests cover 2 of ~24 screens —
  representative, not exhaustive).
- Golden tests, a real DevTools pass, a real TalkBack/VoiceOver pass,
  platform folders, app icon/splash/store metadata, and integration
  tests against a real backend instance all remain undone, blocked on a
  real Flutter SDK/device or a real backend deployment this sandbox
  cannot provide — not a scope gap in this roadmap's own planning.

## Final architecture assessment

Six phases (Steps 1-6) built, in order: the core networking layer, real
authentication, five real `ApiXRepository` implementations against the
real backend (Coach's own research-backed confirmation that it needs
none), a shared offline-caching layer, a performance/accessibility
audit, and this testing/release-readiness validation pass. Every
`docs/adr/00xx` this roadmap produced (0043 through 0054) documents a
real, traceable decision — no undocumented architecture exists anywhere
in `apps/mobile/lib/`. The six-module Clean Architecture layering
(`domain/ -> application/ -> infrastructure/ -> presentation/`)
established before this roadmap began held, unmodified in shape, through
every one of these six phases: not one feature's domain model, repository
interface, or presentation contract needed to change to accommodate a
real backend, a cache, or this phase's own testing work — the one
exception being the two small, disclosed, pre-integration renames/
additive-parameter changes ADR 0042 itself anticipated (`TodayController`/
`fetchToday()`, and `LocalCache`/`forceRefresh`-shaped additive
constructor parameters). `docs/TECH_DEBT.md`'s fourteen items, taken
together, are this project's own honest, trigger-conditioned account of
every real gap and trade-off — none silently dropped, none fixed by
being redefined away.

## Verification performed

No Flutter SDK is available in this environment (`docs/adr/0002`,
unchanged across all six phases) — this phase's verification is the
same static, structural review every prior phase disclosed: every new/
modified test file re-read in full for import correctness, provider-
override completeness, and finder-cardinality correctness (`findsWidgets`
vs. `findsOneWidget` where a previous route stays mounted underneath a
pushed one — the same pattern this suite's own existing tests already
established and this phase's new test follows); `main.dart`, every real
repository's own doc comment, and `pubspec.yaml` re-read in full against
current behavior; `grep` sweeps for `TODO`/`FIXME`, stale "not yet wired"
language, `errorBuilder`, `matchesGoldenFile`, and `meetsGuideline` across
`lib/` and `test/`. `flutter pub get`/`flutter analyze`/`flutter test`
remain the first real verification this phase's own changes get, exactly
as every prior phase disclosed.

## Consequences

This concludes the planned roadmap from `docs/adr/0042-production-
integration-plan.md`. The app is structurally complete and internally
consistent against everything that plan scoped; what remains is
execution-dependent (a real device, a real backend deployment, a real
app-store submission process) rather than undesigned or unplanned. No
further phase is started by this ADR.
