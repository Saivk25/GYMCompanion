# ADR 0038: Fuel module — manual logging as the real path, not a fallback

- Status: accepted
- Date: 2026-08-07

## Context

Today (ADR 0036) and Train (ADR 0037) established the pattern this phase
continues unchanged: `domain/application/infrastructure/presentation`,
a repository interface behind a Riverpod provider, a disclosed mock
implementation, root-navigator routes for full-screen drill-ins, and
honest "not connected yet" placeholders where a backend capability
genuinely does not exist. This phase applies that pattern to Fuel — the
UX/UI Design Bible's nutrition module (Section 5.10, Section 5.3,
Section 5.11's catalog).

Research before any screen was built turned up one finding that shapes
the entire module, more centrally than either backend gap Train found:

**The backend's meal-logging model is pure manual macro entry — there is
no AI/vision capability anywhere in it.** `NutritionSource`
(`backend/app/domain/nutrition/enums.py`) has exactly three values —
`manual`, `barcode`, `import` — no `photo` or `vision` value at all.
`RecordNutritionRequest` (`backend/app/api/schemas/nutrition.py`) takes
raw numbers (`calories`, `protein`, `carbohydrates`, `fat`, `fiber`,
`sugar`) directly; there is no photo field, no confidence field, no
assessment field. The Bible's own Section 5.3 ("Meal Review/Confirm")
describes a screen whose entire purpose is reviewing an AI's reading
before it counts — but there is no AI reading to review. This is not
"the Flutter client isn't wired to the vision endpoint yet" (Today's own
kind of gap) — it is "no vision endpoint, and no concept of one, exists
in this backend at all."

A second, smaller finding: `Nutrition` is a per-entry log, not a daily
rollup (`docs/adr/0011-nutrition-is-a-per-entry-log-not-a-daily-
rollup.md`, backend) — a single record shape carries meal macros *or*
`water_intake` *or* both. There is no separate water-logging endpoint;
logging water is just a `Nutrition` entry with only `water_intake` set.

## Decision

### 1. Capture and Confirm collapse into one real screen: `LogMealScreen`

Section 5.3's spec assumes an AI step happens between capture and
confirm. With no AI step, there is nothing to separately confirm —
typing the numbers *is* the confirmation. Building a second screen that
performatively "reviews" a reading that was never AI-generated would
have been exactly the "fake successful operation" this module's
directive forbids. `LogMealScreen` is Capture and Confirm as one
interaction: choose a meal type, enter what's known, submit.

### 2. Photo and Menu modes are visible, real UI — showing a disclosed gap, not hidden

`LogMealScreen` still offers all three modes the Bible names (Photo,
Text, Menu) via `AppSegmentedControl` — but Photo and Menu render
`NotConnectedPlaceholder` (promoted this phase to `lib/shared/
presentation/`, see Decision 5) instead of a camera flow, with a direct
"Use text entry instead" action. This is not an invented workaround:
the Bible's own empty-states table (Section 15) already prescribes this
exact fallback for a *denied camera permission* — "text/menu-typing
entry remains fully available, framed as an equal option, not a
degraded fallback." The same framing applies whether the camera is
unavailable for a permissions reason or because no vision backend
exists yet to receive the photo; this decision reuses the Bible's own
established language rather than inventing a new posture for a new kind
of gap.

### 3. Two more honest placeholders: Food Search, Supplements

Neither has any backend support at all — no food-database/barcode-
lookup endpoint (`NutritionSource.BARCODE` is a documented-but-
unimplemented enum value, not a live capability) and no supplement
domain concept anywhere in the backend. Both get real, reachable screens
with `NotConnectedPlaceholder`, the same posture Train's Personal
Records and Exercise Library established for comparably total gaps —
not skipped, not faked.

### 4. No separate "Nutrition History" screen for Fuel

The Bible's own Fuel catalog (Section 5.11) lists Meal capture, Menu
interpreter result, Hydration quick-log, and Supplement log/schedule —
no history-list screen. "Nutrition dashboard" (trend/pattern view)
explicitly lives in **Progress**, not Fuel. This is a deliberate Bible
design choice, not an oversight: Section 12/598's own reasoning — "leads
with pattern, never a daily number, to avoid per-meal moralizing" —
argues against a day-by-day meal browser existing anywhere in this app.
Fuel Home's "Today" list already covers the one day-level view the
Bible does specify; inventing a second mid-tier history screen the
Bible doesn't call for would have violated this module's own "do not
simplify — or embellish — screens the Bible doesn't specify" directive
in the invent-more direction, not just the cut-corners one. Fuel Home's
weekly-pattern row instead does real navigation to the existing
`/progress` tab (Section 5.10's own stated exit point: "Pattern tap ->
Progress > Nutrition dashboard") — honest about Progress being unbuilt
itself, rather than Fuel fabricating a dashboard to fill that gap.

### 5. Two components promoted out of Train, once Fuel needed them too

- **`AppProgressBar`** (`design/components/`) — was Train-local
  `SessionProgressBar`; Fuel's hydration progress needed the identical
  flat two-tone bar. Promoted to the design system proper (not
  `lib/shared/`) because a progress meter is a generic visual primitive,
  the same category `AppBadge`/`AppCard` already occupy.
- **`NotConnectedPlaceholder`** — was Train-local; promoted to
  `lib/shared/presentation/widgets/` instead of `lib/design/`, because
  what it discloses is a specific *product* convention (how this app
  talks about an unconnected backend), not a generic visual token.

Both are the literal application of this module's own instruction: "if
duplication appears, improve the design system instead of duplicating
UI" — enforced the moment a second feature needed the same thing, not
guessed at ahead of time.

### 6. Today's Quick Add "Log water" now opens the real `WaterLogSheet`

Reused directly from Fuel rather than duplicated — the same cross-
feature import precedent `AppShell`'s own FAB already set for Today, and
Train's Pre-session screen calling into Today's session card did.
Because Riverpod's `ProviderScope` is app-wide, logging water from
Today's sheet updates the same `fuelHomeControllerProvider` state Fuel
Home reads — the two surfaces stay consistent with no extra plumbing.

## Consequences

**Manual entry is the fully real path for meal logging; Photo/Menu
capture, Food Search, and Supplements are disclosed placeholders.** This
is a materially larger scope boundary than Train's (which had two
placeholder screens against otherwise-complete backend support) — Fuel's
core AI-assisted capture flow the Bible spends the most words specifying
is the one part that cannot be built for real yet. This is disclosed
here and in every relevant screen's own doc comment, not smoothed over.

**`MockFuelRepository` is stateful**, like `MockTrainRepository` and
unlike `MockTodayRepository` — a logged meal or water entry must be
visible on the next fetch. It keeps an in-memory `List<FuelEntry>`,
seeded with one meal and one water entry so Fuel Home never opens
looking artificially bare, reset on every app restart.

**The weekly protein-consistency line is disclosed mock text**, not a
computed result — a real figure needs the `NutritionRuleEngine`'s own
historical-trend logic (`backend/app/domain/nutrition/rules`), Progress-
dashboard territory this module doesn't reach into, the same restraint
Today's own `oneLineSummary` preview already established.

**A fixed 2000ml daily water target is used**, since no personalized
hydration goal exists anywhere in the domain model — disclosed at its
declaration (`fuel_home_screen.dart`), not presented as computed.

**Still hand-authored, structurally verified — not run in this
sandbox.** Every file in this phase inherits ADR 0002's constraint
unchanged. `log_meal_flow_test.dart` locates form fields via
`find.widgetWithText(TextField, label)` against `AppTextField`'s
`InputDecoration.labelText` — a standard Flutter testing idiom, but one
this phase could not empirically confirm against a real widget tree
given no SDK is available to run it, the same category of risk ADR 0037
disclosed for Active Workout's Timer-dependent test.
