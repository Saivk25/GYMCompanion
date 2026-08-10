# ADR 0053: Performance and accessibility audit — Step 5 of production integration

- Status: accepted
- Date: 2026-08-11

## Context

Step 5 of `docs/adr/0042-production-integration-plan.md`, scoped explicitly
by the user as **audit-focused, not optimization-focused**: profile and
inspect the current architecture (static analysis, since no Flutter SDK
is available in this environment — `docs/adr/0002`), review rebuild
scope/provider usage/chart repaint/`IndexedStack`/caching interactions/
allocation hotspots, audit accessibility at the composed-screen level
building on the design-system audit already done (`docs/adr/0035`), and
only fix what is clearly justified and low-risk — otherwise document as
a finding.

This ADR exists because two of this phase's own findings are genuine
trade-off decisions, not just observations: which findings were judged
safe to fix immediately, and which were deliberately left as documented,
deferred work because a correct fix requires a design decision this
audit itself shouldn't make unilaterally.

## Performance findings

1. **`ReadinessTimelineScreen` builds its entire history eagerly.** A
   plain `ListView` with a `for` comprehension constructs one
   `ReadinessEntryTile` per check-in the user has ever logged
   (`data.entries`, sourced from `GET /api/v1/readiness`, which — per
   ADR 0042 Part 2's own "no pagination exists anywhere" finding — always
   returns the complete, unfiltered history). For a long-tenured daily
   user this could mean hundreds of widgets built on every visit to this
   screen and every rebuild it undergoes. **Not fixed.** The list is
   nested inside one shared `AppCard`/`Column` to get a single
   rounded-corner grouped-card look across every row; converting to
   `ListView.builder` for true lazy building would require either
   per-item corner-radius logic (first/last row only) or a
   `SliverList`-based restructuring — a real layout decision, not a
   mechanical swap, so it's recorded as a finding (`docs/TECH_DEBT.md`
   TD-0010) rather than rushed through in an audit phase.
2. **`preSessionControllerProvider`/`activeSessionControllerProvider`
   have no `.autoDispose`.** Both are `AsyncNotifierProvider.family`
   keyed by `workoutId`/`sessionId`; every distinct workout previewed or
   session opened in one app run keeps its own provider instance (and
   last-known `TrainWorkout`/`TrainSession`) resident for the rest of
   that run. For typical usage (a handful of workouts/sessions per day)
   this is negligible; for a user who browses many different workouts in
   one long-lived session it is unbounded growth. **Not fixed.** Adding
   `.autoDispose` interacts with `StatefulShellRoute.indexedStack`'s own
   state-preservation guarantee (Decision 3 below) — whether a
   `PreSessionScreen`/`ActiveWorkoutScreen` popped off the root navigator
   should lose its provider state immediately or only when memory
   pressure demands it is a real product decision (does re-opening the
   same workout a minute later show a stale preview or refetch?), not a
   safe default to flip during an audit. Recorded as
   `docs/TECH_DEBT.md` TD-0011.
3. **The unbounded-history finding compounds with Step 4's cache.**
   `LocalCache.read()`/`readThroughCache` (`docs/adr/0052`) synchronously
   `jsonDecode`/`jsonEncode` the same unpaginated lists on the main
   isolate. This is not a new hotspot Step 4 introduced — it inherits
   ADR 0042 Part 2's pre-existing "no pagination" finding — but it means
   the same unbounded payload now exists in two places (the raw cached
   JSON and the eagerly-built widget tree). Both trace back to the same
   root cause and the same fix (server-side pagination, which is a
   backend change outside this phase's scope) — see TD-0010's own
   trigger conditions.
4. **`AppLineChart._AppLineChartPainter.shouldRepaint`'s list-identity
   check is effectively inert.** Every call site constructs `values`/
   `rawValues` fresh (via a `for` comprehension) on every parent rebuild,
   so `oldDelegate.values != values` is true almost every time
   regardless of whether the underlying numbers actually changed —
   `shouldRepaint` doesn't meaningfully suppress any repaint in practice.
   This is informational, not a defect: chart repaints already only
   happen when `ProgressHomeController`'s state changes (a real fetch or
   mutation), never per-frame or on unrelated rebuilds, so the
   ineffective check costs nothing measurable. Not fixed; not worth a
   `TECH_DEBT` entry (no concrete trigger condition would ever fire on
   its own — it would only matter if this chart were ever driven by a
   much higher-frequency data source, which nothing in this app's actual
   design calls for).
5. **`StatefulShellRoute.indexedStack`/`AppShell` verified correct.**
   Each tab keeps its own nested `Navigator` and scroll position via
   `go_router`'s own `StatefulNavigationShell`; `AppShell.build` reads
   `navigationShell.currentIndex` directly (no extra `ref.watch`), and
   the one `ref.read` inside it is scoped to the logout button's
   `onPressed` callback, not the build method. No over-rebuild pattern
   found.
6. **Provider watch granularity is standard and appropriate; `.select()`
   is unused app-wide.** Every screen is a `ConsumerWidget` watching
   exactly one `AsyncValue<XViewState>` at its root — no nested
   `Consumer` scoping, no per-item re-watching inside list builders. This
   is the correct granularity for this app's actual update frequency
   (state changes on fetch/mutation completion, never per-frame), so the
   absence of `.select()` is not a finding on its own. One narrower,
   related observation: `ReadinessEntryDetailScreen`,
   `ReadinessCheckInScreen`, `MeasurementTrendScreen`, and
   `CoachSignalDetailScreen` each watch their *entire* parent Home
   provider to display one entry/aggregate by id, so each rebuilds on any
   Home-state change, not only a change to the one item shown. Minor,
   consistent with how those screens source their data (no per-entity
   fetch endpoint exists for any of them), not worth a scoped fix on its
   own.

## Accessibility findings

1. **`ExerciseNav`'s exercise-switcher chip was 40dp tall — below the
   48dp minimum this app's design system otherwise enforces
   (`docs/adr/0035`).** **Fixed** — see below.
2. **`LoggedSetRow`'s "Mark complete" tap target is likely smaller than
   its own row's 48dp `ConstrainedBox`.** The `ConstrainedBox(minHeight:
   kMinInteractiveDimension)` wraps the whole `Row`, but the `InkWell`
   wraps only the padded "Mark complete" text — a `Row`'s default
   `CrossAxisAlignment.center` does not stretch children to fill the
   row's height, so the actual gesture-detection area is only as tall as
   the padding-plus-text-line-height around it (well under 48dp). **Not
   fixed.** This list stacks many sets per exercise; widening the tap
   target to the full row height risks visually and functionally
   colliding with adjacent rows in a screen this app's own Active Workout
   design deliberately keeps dense. Recorded as `docs/TECH_DEBT.md`
   TD-0012 rather than fixed as a rushed, unreviewed density change.
3. **Three multi-field forms have no keyboard focus chaining.**
   `LogMealScreen` (~8 fields), `LogMeasurementScreen` (~11 fields), and
   `ReadinessCheckInScreen` (~6 fields) never set `textInputAction`/wire
   a `FocusNode` — `AppTextField` already exposes both parameters, and
   `LoginScreen`/`RegisterScreen` already use them, so this is an
   inconsistency, not a missing capability. Without it, the on-screen
   keyboard's "Next" action does not advance focus field-to-field; a user
   must manually dismiss the keyboard and tap into each field in turn.
   **Not fixed.** Wiring `FocusNode` chaining correctly across three
   forms with 6-11 fields each — with correct disposal, correct
   traversal order, and no behavior change to existing submit paths — is
   real, multi-file work with real dispose-safety risk if rushed through
   an audit pass; recorded as `docs/TECH_DEBT.md` TD-0013.
4. **Dynamic Type: no `textScaleFactor`/`textScaler` override anywhere in
   the app.** System accessibility text scaling passes through unclamped
   everywhere — the correct default posture. No composed-screen fixed-
   height-wrapping-`Text` clipping pattern was found.
5. **Reduced motion: no composed-screen-level animation exists at all.**
   A search for `AnimatedContainer`/`AnimatedSwitcher`/
   `AnimationController`/`Hero`/`TweenAnimationBuilder`/`AnimatedOpacity`
   across every `lib/features/**` file returned zero matches. The only
   animation-bearing widgets in the app are design-system primitives
   (`AppSkeletonBox`), already audited and fixed for
   `MediaQuery.disableAnimations` respect in `docs/adr/0035`. `Active
   WorkoutScreen`'s rest/elapsed timers use `Timer.periodic` to update
   plain numeric text once per second — an informational update, not a
   motion effect, so reduced-motion accommodation does not apply to it.
   No new gap found.
6. **Semantics: no gaps found at the composed-screen level.** Every
   icon-only `IconButton` across every screen sets `tooltip` (Flutter
   derives `Semantics` from it automatically); every list-row across
   every feature reuses `AppListTile`, which already carries the design
   system's own semantics treatment from `docs/adr/0035`. `AppLineChart`/
   `AppWeekHeatmap` both already wrap their `CustomPaint`/decorative
   content in `Semantics(label: ...)` + `ExcludeSemantics`, with a
   required (non-optional) `semanticLabel` parameter forcing every call
   site to describe the chart in words.

## Fixes applied

**`ExerciseNav._NavChip` height: 40 → 48dp**
(`lib/features/train/presentation/widgets/exercise_nav.dart`). Chosen
because it is genuinely low-risk: an isolated, fixed-height horizontal
scroller with no competing row-density constraint (unlike
`LoggedSetRow`), a pure numeric constant change with no downstream
layout dependency, and it closes a concrete, already-established 48dp
guideline this app's own design system already enforces everywhere else.
No test referenced the old height value.

No other fix met this phase's own "clearly justified and low-risk" bar —
every other finding above either requires a design decision (grouped-
card list virtualization, tap-target-vs-density trade-off, focus-order
design across three different forms) or has no concrete trigger
justifying a change today (the inert `shouldRepaint` check, the
`.autoDispose` question). Each is recorded in `docs/TECH_DEBT.md` with
its own trigger condition instead.

## Verification performed

No Flutter SDK is available in this environment (`docs/adr/0002`,
unchanged) — this entire phase is static analysis: manual reading of
`lib/shell/`, every `*HomeScreen`/`*Controller` pair, both chart
components, `lib/core/cache/`, and every composed-screen form/list/
button call site, cross-referenced against `docs/adr/0035`'s own prior
design-system-level accessibility findings to avoid re-auditing what that
phase already covered. `flutter analyze`/`flutter test`/a real-device
accessibility pass (VoiceOver/TalkBack, Dynamic Type at its largest
setting) remain the first real verification this phase's findings get,
per ADR 0002's own disclosure, unchanged from every prior phase.

## Remaining gaps / TECH_DEBT updates

New items: TD-0010 (Readiness Timeline's eager, unbounded list), TD-0011
(`.autoDispose` question for `PreSessionController`/
`ActiveSessionController`), TD-0012 (`LoggedSetRow` touch target),
TD-0013 (focus chaining across three multi-field forms). See
`docs/TECH_DEBT.md` for each item's own trigger conditions.

## Consequences

Step 5 of `docs/adr/0042-production-integration-plan.md` is complete as
an audit: one low-risk, clearly-justified fix applied; four real findings
recorded with concrete evidence and trigger conditions rather than
patched speculatively. No architectural change was made to rebuild
scope, provider structure, caching, or navigation — every mechanism
audited (`StatefulShellRoute.indexedStack`, Riverpod provider
granularity, `readThroughCache`, hand-rolled chart painters) was found
structurally sound for this app's actual scale and update frequency.
