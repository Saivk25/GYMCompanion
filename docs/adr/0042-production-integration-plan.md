# ADR 0042: Production integration plan — architecture audit, backend wiring, offline, performance, accessibility, testing, and release readiness

- Status: accepted (planning only — see Consequences for exactly what has and has not been implemented)
- Date: 2026-08-08

## Context

The Flutter UI foundation is complete: Design System, Today, Train,
Fuel, Progress, Readiness, and Coach (ADRs 0034/0036/0037/0038/0039/
0040/0041) all exist, each built against a disclosed, in-memory mock
repository behind a real repository interface — never a real HTTP
client, never real persistence, never real authentication. The
directive that produced this ADR asked for two things in this pass: a
complete, read-only architecture audit (no code changes), and a
production-integration *plan* (Phases 2-7 below), explicitly stopping
short of implementation unless separately requested. Everything in this
ADR is therefore a finding or a plan, not a changelog — see
Consequences for the one exception (two documentation files: this ADR
and `docs/TECH_DEBT.md`).

The audit was performed by direct inspection of every file in
`apps/mobile/lib/` and `apps/mobile/test/` (105 and 15 files
respectively) — a full folder-structure enumeration, an automated
cross-feature-import sweep, a design-system-bypass sweep (bare
`Icons.*`, hardcoded `Color(0x`, hardcoded `TextStyle(`), a dead-file
sweep (every file checked for at least one real import elsewhere), a
provider-declaration sweep, and a route-table read of the entire
`app_router.dart`. The backend research for Phase 2 was performed by
reading `app/api/routes/auth.py`, `app/api/schemas/auth.py`,
`app/api/errors.py`, `app/api/schemas/common.py`, and one full list/get/
update route triad (`app/api/routes/v1/workout.py`) — the same backend
this project has built and verified over the entire preceding sequence
of ADRs, so this phase re-reads it for the mobile client's sake rather
than re-deriving it.

## Decision

### Part 1 — Architecture Review

**Folder structure and feature boundaries: consistent, no violations
beyond one disclosed exception.** All seven modules follow the same
`domain/ -> application/ -> infrastructure/ -> presentation/` layering
with zero deviation. A full cross-feature-import sweep (every `import`
line in `lib/features/**` checked for whether it points into a
different feature) found exactly one cross-feature presentation-layer
import in the entire codebase: `today/presentation/widgets/
quick_add_sheet.dart` importing `fuel/presentation/widgets/
water_log_sheet.dart` directly. This is not new — it is a disclosed
decision from ADR 0037 — but it is the one real feature-boundary
exception in the app, now tracked as **TD-0005** in `docs/TECH_DEBT.md`
rather than left as an unrecorded fact only visible by reading ADR
0037's prose. Every other cross-feature reference in the app
(`CoachSignalLog`, `CoachSignal`, `SessionTier`, `NotConnectedPlaceholder`)
correctly goes through `lib/shared/`, never directly into another
feature's folder — the boundary discipline established across ADRs
0037-0041 held.

**Dependency direction: correct everywhere it was checked.**
`lib/design/` has zero imports of `lib/features/` or `lib/shell/`
(confirmed by grep — the design system depends on nothing above it).
`lib/shared/` has zero imports of `lib/features/` (confirmed) — the
write-direction dependency Readiness/Fuel/Train have *into*
`CoachSignalLog` is a call from feature to shared, never the reverse.
`lib/shell/` imports every feature's presentation entry point (as it
must, to build the route table) and nothing deeper. No cycle exists
anywhere in this graph.

**Provider ownership: one repository provider and one home controller
per feature, uniformly named, uniformly scoped.** Every feature module
declares exactly one `Provider<XRepository>` (throws by default, per
ADR 0036's original "fail loud, not silent" decision, still true in
`main.dart` today) and exactly one `AsyncNotifierProvider<XHomeController,
XHomeViewState>` — six features, twelve providers, no duplication, no
feature holding two competing sources of truth for the same data.
Train's `PreSessionController`/`ActiveSessionController` are the one
justified exception (`AsyncNotifierProviderFamily`, keyed by
workout/session id — a real, disclosed need from ADR 0037, not
duplication). `CoachSignalLog`'s own `NotifierProvider` is the one
plain `Notifier` (not `AsyncNotifier`) in the codebase, and the one
provider four different features touch — `coachSignalLogProvider` is
read by Coach and written by Readiness/Fuel/Train, all disclosed in ADR
0041. `main.dart`'s override list is consistent: every mock repository
uses `overrideWithValue` except `coachRepositoryProvider`, which
correctly uses `overrideWith` because `MockCoachRepository` needs a
closure capturing `ref` at override time — the one real API-shape
reason for the one exception, not an inconsistency.

**Navigation and routing: complete, no orphaned or unreachable routes,
one real gap.** The full `app_router.dart` was read end to end: five
`StatefulShellBranch` tab roots, and every drill-in screen across
Train/Fuel/Progress/Readiness/Coach reachable via a `parentNavigatorKey:
_rootNavigatorKey` root-level `GoRoute`, following one consistent
pattern (documented once, in the comment above Train's routes, and
referenced rather than repeated by every later module's own routes).
Every screen file that exists is reachable from the route table; no
dead screens. The one real gap: `GoRouter` has no `errorBuilder`
configured, so an unmatched route currently falls through to Flutter's
default, unbranded error widget rather than a designed one — a
concrete, small Phase 7 item (see Part 7 below), not a structural
problem.

**Shared components: fully utilized, no dead component.** Every
component the design system exports (`AppButton`, `AppCard`, `AppBadge`,
`AppListTile`, `AppSectionHeader`, `AppEmptyState`, `AppErrorState`,
`AppSkeletonBox`, `AppProgressBar`, `AppLineChart`, `AppWeekHeatmap`,
`AppSegmentedControl`, `AppRatingSlider`, `AppTextField`) is used at
least once outside `lib/design/` — confirmed by an explicit per-component
usage count. `AppWeekHeatmap` and `AppRatingSlider` are each used in
exactly one place (Progress's Nutrition consistency heatmap; Readiness's
check-in sliders respectively) — low usage, but real usage, not dead
code; both were purpose-built for the one screen that needed them
(ADRs 0039/0040) and nothing since has needed a second consumer.

**Duplicated code: one real, worth-fixing instance found.** A dead-file
sweep (every non-design-system file checked for at least one import
reference elsewhere) found zero unused files — every screen, widget,
controller, and repository in the codebase is reachable and imported.
The one real duplication is presentation-layer date formatting: at
least seven files independently define their own `_formattedDate`/
`_formattedDateTime`/`_formattedDuration` helper, each with its own
literal month-name array, producing three genuinely different output
shapes across the app. Tracked as **TD-0004**. No duplicated domain
models, no duplicated repository logic, and no duplicated business
logic were found — the one thing every module's own ADR was most
careful to avoid (never reimplementing a backend rule engine
client-side) held under this audit too.

**Design-system violations: isolated entirely to `app_shell.dart`.**
The bare-`Icons.*` sweep found zero violations inside any feature
module — every feature screen correctly routes icons through
`AppIcons`. `lib/shell/app_shell.dart` is the one exception: four of
its five tab destinations (Today/Train/Fuel/Progress — Coach was fixed
in ADR 0041) and its entire top app bar (search, notifications,
settings, the location chip) use bare `Icons.*` literals, even though
every one of those exact icons already has a matching `AppIcons` token
sitting unused in `app_icons.dart`. Compounding this, three of the top
bar's buttons (`search`, `notifications`, `settings`) have
`onPressed: () {}` and the location chip has `onDeleted: null` — four
controls that visibly do nothing. Both are tracked together as
**TD-0003**, since fixing the icon references without first deciding
what the four dead controls should actually do would be an incomplete
fix. The only other bypass findings were four instances of
`textTheme.X ?? const TextStyle()` — a null-safety fallback for a
theoretically-absent `TextTheme` entry, not a real hardcoded style, and
one `EdgeInsets.all(8.0)` in `app_shell.dart` rather than an
`AppSpacing` token (folded into TD-0003's scope rather than opened as
its own item, since it's in the same file already being fixed there).

**Naming consistency: one minor, historical inconsistency, otherwise
uniform.** Repository interface methods are uniformly `fetchHome()`
across Train/Fuel/Progress/Readiness; Today's is `fetchToday()` and
its controller is `TodayController`, not `TodayHomeController` — Today
was the first module built (ADR 0036), before the `XHomeController`/
`fetchHome()` convention emerged with Train (ADR 0037), and nothing
since has renamed it. This is cosmetic, not a bug, and is noted here
rather than opened as its own tech-debt item since renaming
`TodayController`/`fetchToday()` is a trivial rename with no design
question attached — folded into the Phase 2 integration work below,
since every repository interface will already be touched then.

**Test coverage: real, but uneven across screens.** Every feature has
at least one widget test exercising its home screen's loading/empty/
error states, following the same skeleton established in ADR 0036.
Drill-in and placeholder screens are covered unevenly: Train has 6
screens behind 3 test files, Progress 6 behind 2, Readiness 5 behind 2,
Fuel 4 behind 2, Coach 4 behind 2 — some of that gap is legitimate
(several drill-ins are exercised incidentally inside a home-screen
test's own navigation flow rather than getting a dedicated file), but
no golden tests, no dedicated accessibility test, and no navigation-
specific test suite exist beyond `app_shell_test.dart`'s five-tab
smoke test. This is expanded into a concrete plan in Part 6.

### Part 2 — Production Integration Plan

**The backend's real shape, as it affects this plan** (re-confirmed by
direct reading, not assumed from memory): authentication is a real,
complete five-endpoint flow (`POST /register`, `POST /login`,
`POST /refresh`, `POST /logout`, `GET /me`), root-level and unprefixed;
every other route lives under `/api/v1` and requires a bearer token via
`get_current_user_id`. Every mutation endpoint returns `IdResponse
{id, warnings}` only — **never the full updated resource** — by
deliberate design (ADR 0031 decision 5, re-confirmed here), so a real
repository's mutation methods cannot simply deserialize the mutation
response the way every mock's `logMeal`/`completeSession`/
`submitCheckIn` does today; each must issue the mutation call, then a
second GET to fetch the view the screen actually needs. Every failure
path funnels through one `ErrorResponse{detail: str | list[str]}`
envelope with a small, fully-enumerated status-code set (400, 401, 403,
404, 422, 500) — a real client-side benefit, since one exception type
with one status-code switch can classify every possible backend failure
without guessing at a shape. **No pagination exists anywhere** — every
list endpoint returns the full collection with no limit/offset/cursor
parameter (confirmed by reading every `@router.get` list-endpoint
signature across Goal/Nutrition/Progress/Readiness/Workout) — so the
"pagination (if supported)" item in the original directive resolves to:
not supported, not planned, until the backend adds it.

**Planned shape of the integration, not yet built:**

1. **API client.** One small HTTP client wrapper (`lib/core/api/` or
   similar — a new top-level folder, since no feature owns "talk to the
   network" as a concept) around a single HTTP package addition (`dio`
   or `http` — neither is a current dependency; this is a real,
   disclosed new dependency, not an existing one this plan is hiding).
   Responsibilities: attach the bearer token from wherever Phase 2's
   token storage lands, serialize/deserialize JSON, and translate every
   non-2xx response into one shared `ApiException` carrying the real
   backend status code and `detail` — never a per-feature reimplementation
   of HTTP handling.
2. **Authentication.** A new `lib/features/auth/` module (the one
   plausible new feature screen this phase's own "do not create new
   feature screens unless a real gap is discovered" instruction
   licenses — there is no existing screen this could be folded into;
   login/register are their own real gap) following the same
   `domain/application/infrastructure/presentation` shape as every
   other feature, holding the access/refresh token pair (a secure-
   storage package, e.g. `flutter_secure_storage` — another real, new
   dependency) and exposing an `authControllerProvider` every other
   repository's real implementation depends on for its bearer token.
   `GoRouter`'s `redirect` callback gains a real auth guard for the
   first time (currently absent — there is nothing to guard, since
   nothing is real yet).
3. **Repository implementations.** Each feature's existing
   `XRepository` *interface* is the real integration seam — ADR 0036's
   original decision to define the interface before any mock existed is
   what makes this phase additive, not a rewrite: a new
   `ApiXRepository` class per feature, implementing the same interface
   the screens already depend on, means zero presentation-layer or
   controller-layer changes are required by this phase in principle.
   In practice, two small interface changes are unavoidable and were
   found during this audit's Part 1: `TodayController`/`fetchToday()`
   renamed to match the `XHomeController`/`fetchHome()` convention
   (cosmetic, noted above), and every mutation method's *implementation*
   (not signature) changing from "return the mock's in-memory updated
   state" to "call the mutation endpoint, then re-fetch" as described
   above.
4. **DTO mapping.** One `XDto`/`fromJson` pair per backend resource
   shape per feature, converting the API's real JSON (already a
   deliberately thin, value-object-free shape per `common.py`'s own
   documented reasoning) into this app's existing domain models — the
   same domain models the mocks already produce today, so no domain
   type changes are anticipated.
5. **Error mapping.** One shared `ApiException -> user-facing state`
   mapping, reused by every controller's existing `AsyncValue.error`
   path (already wired into every screen's `AppErrorState`, per every
   module's own "every screen must include Error" requirement) — 401
   specifically triggers the auth module's token-refresh-then-retry
   flow once, before falling back to a real logout if refresh also
   fails; 403/404/422/500 render through the existing `AppErrorState`
   with a message sourced from `detail`.
6. **Loading and refresh.** No change in shape — every controller
   already models loading via `AsyncValue.loading()` and exposes a
   `refresh()` method (ADR 0036's original pattern, unchanged through
   every subsequent module); a real repository's `Future` simply takes
   real network time instead of a mock's fixed short delay.
7. **Optimistic updates.** Deliberately **not planned for this pass.**
   Every mutation this app performs returns real advisory `warnings`
   the user should see before the UI commits to a new state (this is
   the entire premise of Coach, ADR 0041) — an optimistic update that
   shows success before the server confirms would either have to hide
   those warnings or retroactively contradict itself, neither of which
   is acceptable given how central "never fabricate confidence" has
   been to every module's own design philosophy. Every mutation stays
   pessimistic: show loading, wait for the real response, then update.
8. **Pagination.** Not applicable — see the backend finding above.

### Part 3 — Offline Strategy

**Scoped down from the original request, and the reason is a backend
fact, not a Flutter limitation.** "Only if supported by the backend
architecture" was the directive's own condition on this phase, and the
backend supports none of stale-while-revalidate, a retry queue, sync,
or conflict handling as *server* concepts — there is no `updated_at`-
based conflict field, no idempotency-key mechanism, and no batch/sync
endpoint anywhere in the API layer (confirmed by the same route reading
in Part 2). Building a client-side retry queue or conflict-resolution
UI against a backend with no matching concept on the other end would
mean inventing behavior the server cannot participate in — exactly what
the "never invent intelligence/capability the backend cannot support"
discipline every module ADR in this project has followed says not to
do.

**What is genuinely supportable, and the plan for it:**

1. **Local cache (read-through).** A lightweight local store (`sqflite`
   or `drift`, or — given this app's actual per-user data volume — a
   simpler key-value cache via `shared_preferences`/`hive` may suffice;
   final choice deferred to implementation time, not decided here) that
   each repository's `fetchHome()`/`fetchX()` writes to on every
   successful real fetch, and reads from immediately on next launch
   before the real network call resolves — a real "show the last known
   state instantly, then update" pattern, genuinely useful and fully
   client-side, no server participation required.
2. **Offline reads.** A direct consequence of the cache above — if the
   network call fails with a connectivity error specifically (not a 4xx/
   5xx), fall back to the last cached `fetchX()` result and surface the
   existing "Offline" state every screen already has a slot for (every
   module's own "every screen must include ... Offline" requirement,
   already built and tested against a mock `isOffline` flag — the real
   plumbing is a real connectivity check, not a new UI state).
3. **Stale-while-revalidate.** Supportable as a pure client-side
   pattern layered on top of items 1-2: serve the cached value
   immediately, kick off a real background refetch, and update the UI
   when it resolves — no backend concept required, since this is purely
   about when the client shows data it already has, not about anything
   the server needs to know.
4. **Retry queue, sync, and conflict handling: not planned.** These
   require the backend half this project's backend does not have. A
   retry queue for failed *mutations* specifically (as opposed to reads)
   is the one item genuinely worth flagging for a future backend ADR —
   if the backend ever gains idempotency keys, this plan's item 4
   should be revisited as a paired Flutter+backend phase, not built
   Flutter-only against a server that cannot deduplicate a retried
   mutation.

### Part 4 — Performance Findings

**These are static-code findings, not measurements — the honest
constraint every prior phase of this Flutter build has operated under
(ADR 0002) still applies: no Flutter SDK exists in this environment, so
nothing here was profiled with DevTools, and "optimize only after
measurement" (the directive's own instruction) is not yet possible to
honor literally. What follows is what a static read can responsibly
surface, and what the actual measurement pass should check first once
a real device/SDK is available.**

1. **`IndexedStack` cost (already disclosed, not new).** ADR 0041
   already documented that `StatefulShellRoute.indexedStack` builds all
   five tab branches' widget trees immediately, including Coach's, on
   first frame — this is `go_router`'s own documented tradeoff for
   preserving each tab's navigation/scroll state, not a bug, but it is
   the single largest "build more than the visible screen" cost in the
   app and the first thing a real DevTools frame-timeline check should
   quantify.
2. **`ConsumerWidget`/`ConsumerStatefulWidget` scope.** Every screen
   audited watches its own `XHomeControllerProvider` at the screen
   root, not narrowed to the specific sub-widget that needs it — the
   same pattern used consistently across all six modules, so there is
   no per-module inconsistency to fix, but it means every `ref.watch`
   at a screen root rebuilds that screen's entire subtree on every
   state change rather than only the affected tile. Real measurement
   (widget rebuild counts via DevTools) should confirm whether this is
   actually costly before doing the work of narrowing `Consumer`
   boundaries — several of these screens (Progress's five-segment
   dashboard, Coach's filtered feed) are exactly the shape where
   narrowing would matter if it matters anywhere.
3. **Image loading: not yet applicable.** No feature currently loads a
   real remote image — Photo Check-in/Comparison are honest
   `NotConnectedPlaceholder`s (ADR 0039), and Fuel's Photo capture path
   is the same (ADR 0038). This becomes a real Phase 4 concern the
   moment either gains a real backend counterpart, not before.
4. **Chart/heatmap rendering.** `AppLineChart` and `AppWeekHeatmap`
   (ADR 0039) are the only custom-painted, non-trivial-layout widgets in
   the app — the first place to check for excess repaints once real
   measurement is possible, since a `CustomPainter` repainting on every
   parent rebuild (rather than only when its own data changes) is the
   single most common real Flutter performance bug in exactly this kind
   of widget.
5. **Navigation stack depth.** Bounded and shallow by construction —
   every drill-in route in `app_router.dart` pushes onto the root
   navigator directly from a tab root (never a drill-in from a
   drill-in), so no screen in this app is more than two pushes deep.
   Nothing to fix here; noted as a finding, not a gap.

### Part 5 — Accessibility Findings

**Foundation is real and already verified once** (ADR 0035's own
architecture review computed real WCAG contrast ratios, fixed two real
failures, audited typography under large accessibility text sizes for
every *design-system component*, and gave every tappable target a real
48dp minimum) — this phase's job is to say what that foundation does
and does not cover now that six feature modules' worth of real screens
exist on top of it.

1. **Dynamic Type: verified at the component level, not re-verified at
   the screen level.** ADR 0035 tested each component in isolation
   under large text scale; no feature screen's actual composed layout
   (e.g., Progress's five-segment dashboard, Coach's filtered feed with
   badges and tiles together) has been re-checked for whether components
   that individually handle large text still lay out correctly *next to
   each other* at scale. This is the single largest concrete Phase 5
   gap: a full-screen screenshot-at-max-text-scale pass, per screen, is
   still owed.
2. **Screen reader labels: uneven, likely under-covered outside the
   design system.** Only 7 files in the entire app use an explicit
   `Semantics(...)` widget, and all 7 are either design-system
   components or Train's own custom navigation controls
   (`exercise_nav.dart`, `logged_set_row.dart`, `tier_picker.dart`).
   Every other screen relies entirely on Flutter's implicit semantics
   from standard widgets (`Text`, `Icon`, `IconButton`'s `tooltip`) —
   which is often sufficient, but was not individually verified per
   screen in this pass. A real audit needs a screen reader actually
   turned on (TalkBack/VoiceOver), which this environment cannot do
   (ADR 0002's constraint again) — flagged as the first item that needs
   a real device, not more static reading.
3. **Reduced motion: has real, dedicated infrastructure.**
   `AppMotion`'s own doc comment and `app_states.dart`'s
   `MediaQuery`-based check (both predating this phase, from ADR 0035)
   confirm a real reduced-motion-aware helper already exists and is
   used by `AppSkeletonBox`. Not yet confirmed: whether every
   *feature-specific* animation (Train's rest timer, Readiness's
   check-in slider) also routes through it, versus using `AppMotion`'s
   duration/curve tokens directly without checking the reduced-motion
   flag — worth a targeted grep-and-fix pass, not a redesign.
4. **Touch targets: enforced by the design system, not independently
   re-checked per screen.** ADR 0035's fix was structural (inside
   `AppListTile`/`AppButton`/etc.), so every screen using those
   components inherits the fix automatically — the only real risk is a
   screen using a bare `IconButton`/`GestureDetector` outside the
   design system's own sizing, which the design-system-bypass sweep in
   Part 1 did not find evidence of beyond `app_shell.dart` (TD-0003).
5. **Keyboard navigation.** Not meaningfully applicable to this app's
   actual target (a touch-first mobile client) beyond what Flutter's
   `Focus`/`FocusTraversalGroup` already provides by default for text
   fields (`AppTextField`, used in Log Meal, Log Measurement, Check-in) —
   no custom `FocusNode` management exists anywhere in the app, which
   is appropriate for this app's actual scope rather than a gap, since
   no screen currently requires a custom tab order.

**Fixes:** none applied in this pass — the directive's own closing
instruction stops this phase at planning; "Fix every issue found" (Phase
5's own line) is superseded by the later, more specific "stop after the
audit and production integration planning unless implementation is
explicitly requested." Every item above is therefore a finding with a
named next step, not yet a change.

### Part 6 — Testing Strategy

Current state (Part 1): real widget-test coverage on every home
screen's loading/empty/error/success states, uneven coverage on
drill-ins, zero golden tests, zero dedicated accessibility tests, zero
navigation-specific tests beyond the one five-tab smoke test.

**Planned additions, in priority order:**

1. **Repository tests** — once Phase 2's `ApiXRepository` classes exist,
   each needs its own test suite against a mocked HTTP layer (not a
   real network call), verifying real DTO mapping, real error-status
   mapping, and the mutate-then-refetch pattern Part 2 describes. This
   is the highest-priority new test category, since it is the one
   category that does not exist at all today (there was nothing to
   test — the mocks *are* the current "repository implementation").
2. **Golden tests** — one per design-system component first (cheapest,
   highest-value target — a visual regression on `AppCard`/`AppBadge`/
   etc. would otherwise be invisible across all six features at once),
   then the highest-traffic screen per feature (each `XHomeScreen`).
   Explicitly sequenced *after* TD-0004's date-formatting consolidation
   (Part 1) — golden assertions against text that's about to be
   refactored would need rebaselining twice.
3. **Navigation tests** — a real test suite exercising every
   `parentNavigatorKey` drill-in route by path (not just by tapping a
   button that happens to reach it), confirming `context.push`/`pop`
   round-trips correctly restore the originating tab's state — this
   protects the `IndexedStack` architecture Part 4 flagged as this
   app's biggest structural cost, since a regression there is exactly
   the kind of bug that's easy to introduce silently.
4. **Accessibility tests** — `flutter_test`'s own
   `SemanticsTester`/`meetsGuideline` matchers
   (`meetsGuideline(textContrastGuideline)`,
   `meetsGuideline(androidTapTargetGuideline)`) run against every
   screen, once a real Flutter SDK is available to run them (ADR 0002)
   — this is the automatable subset of Part 5's findings; TalkBack/
   VoiceOver verification itself still needs a real device pass.
5. **Widget test gap-filling** — bring Train/Progress/Readiness/Fuel/
   Coach's drill-in-screen coverage ratio up toward Today's 1:1 (Part
   1), prioritizing the screens currently reached only incidentally
   inside another test file's flow.
6. **Integration tests** — end-to-end against a real (test) backend
   instance, not the mocks — genuinely new; nothing like this exists
   today since there has been no real backend connection to integrate
   against until Phase 2 exists.

### Part 7 — Production Polish (release readiness)

Findings, not fixes (same "planning, not implementation" scope as every
other part):

1. **The four dead top-bar controls and four bypassed icon tokens**
   (TD-0003) are the single most visible "looks unfinished" item in the
   app today — a real reviewer (App Store or a first-time user) taps
   Search/Notifications/Settings within the first ten seconds of using
   the app, since they're in the persistent top bar of every single
   screen.
2. **No `GoRouter.errorBuilder`** (Part 1) — an unmatched route
   currently shows Flutter's default red-screen-style error widget, not
   a branded one; low-likelihood in normal use (every real route is
   reachable through real navigation, not user-typed URLs) but a real
   gap for a production build.
3. **Placeholder wording is already handled well, not a gap.** Every
   `NotConnectedPlaceholder` across five modules already uses real,
   specific, non-generic copy naming exactly what's missing (per each
   module's own ADR) — this was checked and found consistent, not
   flagged as an item needing polish.
4. **TD-0004's formatting inconsistency is also a visible polish issue,
   not just a code-duplication one** — a user moving between Train's
   History tab ("Jan 5") and Readiness's Entry Detail ("January 5,
   2026") for dates only days apart sees two different date styles in
   the same session; folding the visual fix into TD-0004's own planned
   consolidation (Part 1) rather than opening a separate item for it.
5. **No app icon, splash screen, or store metadata exists** —
   `flutter create`'s platform folders (`android/`, `ios/`) have never
   been generated in this environment (ADR 0002), so app icon, splash
   screen, bundle identifier, and store listing content are all
   entirely unstarted, not merely unpolished. This belongs at the very
   end of the release checklist below, not folded into any code-level
   polish item.

### Release checklist

Ordered by real dependency, not by the phase numbering above (several
phases must interleave in practice):

1. Generate platform folders (`flutter create --platforms=android,ios`,
   per the mobile README's own first-time-setup instructions) and run
   the full existing test suite on a real device/simulator for the
   first time — the first moment any of this project's Flutter code has
   ever actually executed (ADR 0002's constraint, closed only here).
2. Fix TD-0003 (icon tokens + the four dead top-bar controls) and
   TD-0004 (date-formatting consolidation) — both are pre-integration
   cleanups, cheapest to do before Phase 2 touches the same files.
3. Build Phase 2 (API client, auth module, real repositories, DTO/error
   mapping) against the real backend.
4. Build Phase 3's supportable subset (local cache, offline reads,
   stale-while-revalidate) on top of the now-real repositories.
5. Run a real DevTools performance pass (Part 4) now that the app runs
   on a real device — confirm or refute each static finding before
   spending effort on any of them.
6. Run a real TalkBack/VoiceOver pass (Part 5) and close the Dynamic-
   Type-at-screen-level gap.
7. Build out Part 6's testing plan, in the priority order given there.
8. Add `GoRouter.errorBuilder`, app icon, splash screen, and store
   metadata (Part 7).
9. Full regression pass, then submission.

## Consequences

**This ADR is itself the only artifact this phase produced beyond
`docs/TECH_DEBT.md`'s three new entries (TD-0003, TD-0004, TD-0005).**
No `.dart` file was created, modified, or deleted in this phase — the
directive's own closing line ("Stop after the audit and production
integration planning unless implementation is explicitly requested")
governs this pass exactly as written. Every "Fix every issue found"
instruction inside the original directive's Phase 5 is therefore
deliberately *not* actioned yet; this ADR is the plan for that work,
not the work.

**The plan depends on a real Flutter SDK and a real device far more
than any prior phase did.** Every ADR through 0041 could be fully
verified by static, structural means (ADR 0002's own accepted
constraint). This plan's Parts 4-6 explicitly cannot — DevTools
profiling, TalkBack/VoiceOver, and even `flutter test` itself all
require an environment this sandbox does not have. The release
checklist's own ordering reflects this: step 1 is running the app for
the first time, ever, which nothing before this ADR has done.

**Two new runtime dependencies are anticipated but not yet added.**
An HTTP client (`dio` or `http`) and secure token storage
(`flutter_secure_storage` or equivalent) do not exist in `pubspec.yaml`
today and will be real, disclosed additions the moment Phase 2
implementation begins — flagged here so that addition is not a surprise
when it happens.

**TD-0003/0004/0005 are now tracked with the same trigger-condition
discipline as TD-0001/0002**, per `docs/TECH_DEBT.md`'s own established
convention — none is fixed by this ADR; each has a concrete condition
under which the next unit of work should close it.
