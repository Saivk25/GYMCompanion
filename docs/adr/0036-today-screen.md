# ADR 0036: Today screen — the first real feature screen, and the pattern every later screen inherits

- Status: accepted
- Date: 2026-08-06

## Context

The design system (ADR 0034) and its refinement pass (ADR 0035) are accepted.
Per the standing implementation order, this phase begins Step 13 — feature
screens — starting with Today, the default landing tab and, per the UX/UI
Design Bible Section 5.1, the screen "every comparable screen elsewhere in
the app inherits" its interaction pattern from. Today is also the first
screen in this codebase to need real state, not a static placeholder — so
this phase necessarily also decides how *any* feature screen talks to data,
not just how Today specifically looks.

Two constraints shape every decision below: nothing may look AI-generated,
template-derived, or Material-demo generic (this project's explicit,
standing design requirement), and nothing outside `lib/design/` may
hardcode a color, spacing value, radius, duration, or shadow — every visual
decision must trace to a token or component.

## Decision

### 1. Clean Architecture, client-side: domain → application → infrastructure → presentation

`lib/features/today/` is four packages, mirroring the backend's own
`app/domain` → `app/application` → `app/infra` → `app/api` layering
(Engineering Master Plan's Clean Architecture rule, applied to the client
for the first time):

- `domain/today_models.dart` — pure Dart value types (`ReadinessBand`,
  `SessionTier`, `SessionCardStatus`, `TodaySessionSummary`, `TodayStreak`,
  `TodayTask`, `TodayViewState`). No Flutter import anywhere in this file.
  Naming deliberately mirrors the Domain Model & Decision Engine Bible
  (`RecoveryState`'s `Normal -> Light -> Recovery -> Escalate` band
  lifecycle, Section 7.3; `min/standard/stretch` session tiers; Habit/
  Streak's `current_streak`/grace vocabulary, Section 4.12; Task/
  Recommendation's `user_facing_text`/rationale requirement, Section
  4.13) — so a future real repository mapping API responses onto these
  types is a direct field-for-field translation, never a re-interpretation.
- `application/today_controller.dart` — `TodayRepository` (an abstract
  interface `TodayScreen` never bypasses) and `TodayController`, a thin
  Riverpod `AsyncNotifier<TodayViewState>` whose only job is calling
  `fetchToday()` and re-exposing the result plus a `refresh()` for pull-
  to-refresh and retry.
- `infrastructure/mock_today_repository.dart` — today's only
  `TodayRepository` implementation. See Decision 2.
- `presentation/` — `TodayScreen` (the orchestrator) plus
  `widgets/session_card.dart`, `readiness_checkin_card.dart`,
  `today_task_card.dart`, `quick_add_sheet.dart`. `TodayScreen` itself
  holds no business logic — every branch it renders is read directly off
  `TodayViewState`, never computed.

### 2. A disclosed mock repository, not a half-built API client

`MockTodayRepository` returns a fixed, realistic snapshot instead of a real
network call — and says so, in its own doc comment, in exactly the terms
ADR 0002 already established for a missing Flutter SDK: a disclosed
limitation, not a silently-assumed one. An authenticated HTTP client, local
caching, and offline sync are later, separately-scoped stages of this
project's own implementation order (per the original brief's thirteen-stage
sequence); absorbing all three into "build the Today screen" would have
meant either not shipping a screen at all this phase, or quietly
hand-waving a fake data layer without naming it as one. `TodayRepository`
being an interface `TodayController` depends on (never a concrete class) is
what makes the eventual swap a one-line override in `main.dart`
(`todayRepositoryProvider.overrideWithValue(...)`) rather than a rewrite —
the same seam a widget test's own fake repository already exercises today.

### 3. Riverpod's `AsyncNotifier`, and two levels of "loading/error," not one

`TodayController`'s `AsyncValue<TodayViewState>` (Riverpod's own loading/
data/error) drives exactly one thing: the *page's* first-load skeleton and
a genuine full-page fetch failure (`_TodayPageSkeleton`/`_TodayPageError`).
Everything else — a session-generation failure, an empty-plan onboarding
state, a completed session — is a field on the already-loaded
`TodayViewState` (`sessionStatus`), because the UX/UI Design Bible
describes these as properties of the *session card specifically*, not of
the page ("a calm inline message... rather than a blocking error screen").
Collapsing these into one page-level `AsyncValue` would have made a plan-
generation hiccup blank the entire screen — streak, task card, and
readiness band included — which is exactly the "blocking error screen" the
Bible names and rejects.

### 4. The FAB lives in `AppShell`, not `TodayScreen`

UX/UI Design Bible Section 4: "One FAB, scoped to the Today tab only."
`go_router`'s `StatefulShellRoute.indexedStack` gives each tab its own
navigation stack inside `AppShell`'s single `Scaffold` — there is exactly
one `Scaffold` in this tree, and a per-tab FAB is necessarily that
`Scaffold`'s concern, keyed off `navigationShell.currentIndex == 0`.
`QuickAddSheet`'s *content* (meal/water/note) still lives under
`features/today/presentation/widgets/` and is Today-specific; `AppShell`
only decides *when the FAB appears*, never what it does — a narrow,
justified crossing of the shell/feature boundary, not a precedent for the
shell absorbing feature logic generally.

### 5. Interaction priority and every named state, read directly off the Bible

Every rendering decision in `TodayScreen`/`SessionCard` traces to a
specific line in Section 5.1's fourteen-field specification, not to
inference:

- **Interaction priority** — "A not-yet-completed readiness check-in
  outranks [the session card], appearing above [it] until submitted":
  `_TodayContent` renders `ReadinessCheckInCard` conditionally, first,
  before `SessionCard`, exactly once `state.checkInCompletedToday` is
  `false`.
- **Loading** — "A skeleton card matching the session-card layout — never
  a spinner": `_SessionCardSkeleton` is built from `AppSkeletonBox`
  pieces shaped like `_SessionReadyCard`'s real layout, not a
  `CircularProgressIndicator`.
- **Empty** — "onboarding-continuation card instead of a session card":
  `SessionCardStatus.empty` renders the design system's own
  `AppEmptyState`, not a bespoke widget.
- **Error** — "a calm inline message offers a manual 'browse the exercise
  library' fallback rather than a blocking error screen":
  `SessionCardStatus.error` renders `AppErrorState` with
  `retryLabel: 'Browse exercise library'`, scoped to the session card's
  own slot — every other element on the page still renders normally.
- **Success** — "the two-minute-win option for tomorrow's context stays
  visible, never hidden": `_SessionCompletedCard` keeps the
  two-minute-win `AppButton` visible alongside the "Done for today"
  summary, not gated behind a "come back tomorrow" state.
- **Offline** — "a small offline indicator": one `labelMedium` caption
  line in the header, never a banner or a blocking overlay.

### 6. Readiness band and streak: reusing the existing four-tone badge system, never inventing a fifth

The readiness band (`Normal`/`Light`/`Recovery`/`Escalate`) needed a
visual treatment, and the design system's `AppBadge` already has exactly
four tones. Rather than extending the design system with a new tone (which
the standing rule explicitly permits, "if a required token does not
exist"), `Light` and `Recovery` were verified to both fit
`AppBadgeTone.warning`'s own documented meaning ("reduced-capacity or
caution, never alarmist") — distinguished from each other by label text,
not color, per the Bible's own "no alarm-red overuse" instruction and this
system's color-independent-communication rule. `Normal` uses `.neutral`,
not `.success` — a routine "nothing's wrong" day is not the genuine
achievement `.success` is reserved for (see `AppBadgeTone.success`'s own
doc comment); coloring every ordinary day as an achievement is exactly how
a habit tracker stops meaning anything within a few weeks. `Escalate` uses
`.danger`, the one band that is a genuine safety state. No new badge tone
was needed; extending the design system was correctly judged unnecessary
here rather than reached for by default.

The streak indicator renders as one small `labelMedium` caption line —
deliberately not a badge, not a flame icon, not an accent color. This was
a live design decision, not an oversight: a flame/streak icon is one of
the most immediately recognizable "gamified habit app" signals (Duolingo
and similar), directly opposed to this app's own "no gaming dashboard
aesthetics" principle and the Domain Model Bible's explicit ban on
shame-framed messaging for a *broken* streak — applied here symmetrically
to an *active* one. The Bible's own word for this element, "understated,"
is implemented literally.

### 7. Deferred actions surface honestly, never silently

Every action leading somewhere not yet built (Active Session, the
Readiness Check-in screen, Plan setup, the Exercise Library, water/note
quick-add) shows a small `SnackBar` naming what isn't built yet, via one
shared `_notBuiltYet` helper, rather than doing nothing. A silent no-op is
indistinguishable from a bug; this is the same disclosed-limitation
posture ADR 0002 established for Flutter verification and `AppShell`'s
own pre-existing search/notification icons already used ("render but
carry no behavior yet") — applied consistently to every new deferred
action this phase adds, rather than inventing a new, unstated convention.

## Consequences

**This is the pattern every later feature screen now follows.** Train,
Fuel, Progress, and Coach each get their own `domain/application/
infrastructure/presentation` split, their own `TodayRepository`-shaped
interface, and their own mock-until-real-backend-exists implementation —
this ADR is the reference, not a one-off.

**A real API client, local cache, and offline sync are still not built.**
`MockTodayRepository` is a known, disclosed placeholder; nothing in
`TodayController` or `TodayScreen` needs to change when it is replaced —
only the `main.dart` override and a widget test's fake repository would.

**`AppShell` gained one new responsibility (the conditional FAB) and one
new cross-feature import.** This is the one deliberate, narrow exception
to "shell doesn't know about feature internals" this phase introduces; see
Decision 4 for why it could not reasonably live anywhere else given
`StatefulShellRoute.indexedStack`'s single-`Scaffold` structure.

**`app_shell_test.dart` now requires overriding `todayRepositoryProvider`.**
Every test that boots `GymCompanionApp` lands on `/today` by default; with
no override, `TodayController.build()` throws (by design — see Decision
2), which `AsyncNotifier` converts to an `AsyncValue.error` Riverpod itself
catches, so the app would not have crashed, but Today would have silently
rendered its error fallback in every test that didn't need it, masking
what the test was actually meant to exercise. Both existing tests and this
phase's new `today_screen_test.dart` override the provider explicitly.

**Still hand-authored, structurally verified — not run in this sandbox.**
Every file in this phase inherits ADR 0002's constraint unchanged; see this
phase's own Verification section for what was and was not executed.
