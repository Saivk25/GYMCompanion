# ADR 0035: Design System Refinement — resolving the architecture review's Critical and Important findings

- Status: accepted
- Date: 2026-08-06

## Context

ADR 0034 built the Flutter design system's token/theme/component foundation.
A subsequent, deliberately adversarial Design System Architecture Review (no
code changes, review only) was performed against that foundation and found
four Critical and six Important findings, plus six Nice-to-Have items. The
review was accepted verbatim — every finding number and wording below is the
review's own — with an explicit instruction: resolve every Critical and
Important finding, implement Nice-to-Haves only where they naturally fit
(documenting deferral otherwise), do not introduce new features, do not
redesign the architecture, and stop before any feature screen, navigation,
or authentication UI work begins. This ADR documents what changed and why,
per finding.

## Decision

### Critical 1 — `AppTheme.light`/`.dark` memoized as `static final`

`AppTheme.light`/`.dark` were `static ThemeData get` accessors, re-running
`_build()` — roughly a dozen component sub-theme allocations — on every
single access. Changed to `static final ThemeData light = _build(...)` /
`dark = _build(...)`: Dart evaluates a `static final` initializer exactly
once, lazily, on first access, and caches the result for the process's
lifetime, whereas a getter's body re-runs every time. Since `_build()`'s
output is a pure function of a fixed `ColorScheme`/`AppSemanticColors` pair
(never anything that changes at runtime), there is no correctness reason to
ever recompute it — only a performance cost from doing so. This mirrors the
same fix already applied to `AppSemanticColors.light`/`.dark` in ADR 0034's
implementation.

### Critical 2 — `AppSkeletonBox` never runs its `AnimationController` under reduced motion

The previous implementation created and `repeat()`-ed an `AnimationController`
unconditionally in `initState`, and only consulted `AppMotion.resolve` inside
`build` to decide whether to *paint* the animated result — the ticker itself
kept running every frame regardless, which is exactly the background work
the OS reduced-motion setting exists to eliminate, not just its visible
symptom. `_controller` is now nullable; `didChangeDependencies` (which reruns
whenever the inherited `MediaQuery` changes, including the user toggling
the OS setting mid-session) creates and starts the controller only when
motion is allowed, and disposes it back to `null` the instant it isn't. A
reduced-motion skeleton now never allocates a ticker at all.

### Critical 3 — `AppListTile`/`AppSectionHeader` meet the 48dp minimum touch target

`AppListTile`'s title-only row (no subtitle) laid out to roughly 44px,
under the 48dp minimum both WCAG 2.5.5 and Material specify — a real defect
given this is the app's single most-tapped component (every history entry,
meal, notification). Fixed by wrapping the row's content in
`ConstrainedBox(constraints: BoxConstraints(minHeight: kMinInteractiveDimension))`
rather than adding visible padding: `Row`'s own layout centers its children
within whatever height it is given, so a short row silently gains a couple
of invisible pixels of breathing room instead of visibly growing.

`AppSectionHeader`'s trailing `TextButton` explicitly shrank its own tap
target to `Size.zero` with `MaterialTapTargetSize.shrinkWrap` — undercutting
the 48dp minimum the app-wide `textButtonTheme` (`AppTheme`) already
establishes for every other `TextButton`. Fixed by removing those two local
overrides entirely, so the button inherits the theme's 48pt `minimumSize`
instead of re-deciding it locally. A borderless, fill-less `TextButton`
growing its invisible layout bounds changes nothing anyone can see, only
what they can reliably tap.

### Critical 4 — `AppButton` announces its label while loading

The loading branch replaced `Text(label)` with a bare spinner, dropping the
label a screen reader needs to announce entirely — a loading button
regressed to an unlabeled control. Fixed by wrapping the button's content in
`Semantics(label: label, excludeSemantics: true)`, applied unconditionally
in both the loading and non-loading branches so the announced label never
depends on which internal branch happens to render, and `excludeSemantics`
suppresses the spinner's own unhelpful "progress indicator" semantics node
from taking over.

### Important 5 — one source of truth for `SnackBar` and shadow colors

`app_theme.dart`'s `snackBarTheme` hand-picked `AppColors.neutral100`/
`neutral900` and re-derived, with a local `isDark` branch, the exact
light/dark inversion `ColorScheme.inverseSurface`/`onInverseSurface`/
`inversePrimary` already exist to express — a second, disconnected copy of
one decision. Now reads `colorScheme.inverseSurface` directly, and the
local `isDark` branch it required is gone.

`AppElevation.shadowsFor()` previously computed its own "near-black" shadow
tint internally, independent of `ColorScheme.shadow`. Its signature is now
`shadowsFor(level, {required Brightness brightness, required Color
shadowColor})` — every call site (`AppCard`, the only current consumer)
passes `colorScheme.shadow` in, so shadow color has exactly one source of
truth instead of two that happened to agree by coincidence.

### Important 6 — disabled button styling is consistent across all three variants

Previously, only `elevatedButtonTheme` set disabled colors at all (a
hand-rolled `onSurface.withOpacity(0.12/0.38)` pair); `outlinedButtonTheme`
and `textButtonTheme` had no disabled styling of their own and fell back to
whatever Flutter's `ButtonStyleButton` defaults to internally. All three
button themes now read `disabledBackgroundColor`/`disabledForegroundColor`
from the same named tokens (`AppSemanticColors.disabledContainer`/
`disabledContent` — see Important 7), and `OutlinedButtonThemeData`
additionally dims its border color to `disabledContent` when disabled via a
`WidgetStateProperty<BorderSide?>` override. Primary (`ElevatedButton`),
Secondary (`OutlinedButton`), and Tertiary (`TextButton`) now share one
disabled model, varied only by which of their own colors that model tints.

### Important 7 — Disabled, Focus, and Selection are real, named tokens

`AppSemanticColors` gained six new fields: `disabledContent`,
`disabledContainer`, `focusRing`, `selected`, `onSelected`,
`selectedContainer`. None of these invent a new hue — Material's own
convention (which this system follows) is that disabled always reads as a
dimmed `onSurface` regardless of what it's disabling, focus reuses
`primary` (the color that already means "interactive" everywhere else),
and selection reuses `primaryContainer`/`onPrimaryContainer`. What changed
is that these are now an explicit, reviewable, named home for those
decisions instead of implicit Material defaults nothing in this codebase
had actually decided. Because deriving `disabledContent`/`disabledContainer`
requires real `Color.withOpacity` arithmetic (not `const`-expressible),
`AppSemanticColors.light`/`.dark` moved from `static const` literals to
`static final` values computed once via a private `_build(ColorScheme)`
factory — the same memoization discipline as Critical 1, applied for the
same reason.

### Important 8 — a real, token-driven interaction-state system

`lib/design/tokens/app_opacity.dart` is a new file: `AppOpacity` names
Material 3's own published state-layer opacities (hovered 8%, focused/
pressed 10%, selected 12%, dragged 16%, plus this app's own disabled-content/
container opacities) as reviewable constants, and `AppOpacity.overlayFor(Color)`
builds a `WidgetStateProperty<Color?>` resolving pressed/hovered/focused
overlays from them. This is now wired into every interactive surface this
phase touches: all three button themes' `overlayColor`, `AppCard`'s
`InkWell`, and `navigationBarTheme.overlayColor`. Reusing Material 3's own
published numbers (rather than inventing new ones) means the result still
reads as "subtle, professional, handcrafted" — restrained, not exotic — while
being an explicit, named decision this design system owns and can change in
one place, rather than an unreviewed framework default.

### Important 9 — WCAG contrast was computed, not asserted

Every color pair this design system defines was checked against the real
WCAG relative-luminance contrast formula (a from-scratch Python
implementation, not a lookup table), against the correct threshold for its
role — 4.5:1 for text (WCAG 1.4.3), 3:1 for large text and UI components/
graphical objects (WCAG 1.4.11). Two real failures were found and fixed;
everything else below passed and is recorded as evidence of verification,
not assumed.

**Failures found and fixed:**

| Pair | Role | Before | After | Requirement |
|---|---|---|---|---|
| `outline` (light) on `surface` | `OutlinedButton` border, text-field border, bottom-sheet drag handle | `neutral300`, 1.54:1 | `neutral500`, **3.54:1** | 3.0:1 |
| `outline` (dark) on `surface` | same | `neutral700`, 2.59:1 | `neutral600`, **3.68:1** | 3.0:1 |
| `warning500` (light) on `surface` | `AppSemanticColors.warning` — icon/text-on-fill | `0xFFC98A2E`, 2.93:1 | `0xFFBF832C`, **3.23:1** | 3.0:1 |

The `warning500` fix is a ~5% luminance reduction along the same hue (not a
different color) — chosen with headroom above the 3:1 floor rather than the
minimum value that technically clears it, the same margin-over-minimum
judgment applied to the `outline` fix. `outlineVariant` (dividers only) was
deliberately left unchanged — it is a decorative separator, explicitly
outside WCAG 1.4.11's scope, and its entire purpose is to be quieter than
`outline`; "fixing" it would defeat that purpose for no accessibility gain.

**Representative pairs verified passing** (light theme; dark theme mirrors,
see calculation script for the full set): `onPrimary`/`primary` 5.37:1,
`onSecondary`/`secondary` 7.56:1, `onError`/`error` 4.95:1, `onSurface`/
`surface` 15.07:1, `onSurfaceVariant`/`surface` 5.32:1, `onInverseSurface`/
`inverseSurface` (SnackBar text) 14.31:1, `onSuccessContainer`/
`successContainer` 8.25:1, `onWarningContainer`/`warningContainer` 7.61:1,
`danger500`/`surface` 4.95:1, `danger500` error-border on the raised input
fill 4.42:1, `signal500` focused-border on the raised input fill 4.80:1.
Disabled-state contrast (`disabledContent` on `disabledContainer`) is
deliberately not held to these thresholds — WCAG's own non-text contrast
requirement explicitly exempts disabled UI, since "looks inactive" is the
correct signal there, not "readable at full strength."

### Important 10 — large accessibility text sizes audited across all eight named areas

- **Buttons** (`AppButton`): the label `Text` inside the content `Row` was
  unwrapped — at large text scales, a label plus icon that no longer fit
  the button's width would overflow the `Row` rather than wrap. Now wrapped
  in `Flexible`, so the label wraps onto a second line and grows the button
  (its height was already a minimum, never a fixed cap) instead of clipping
  or overflowing.
- **Section headers** (`AppSectionHeader`): the same risk, for the same
  reason — a long title alongside a trailing action could overflow the
  `Row`. The title is now wrapped in `Expanded`, which also makes the
  previous explicit `mainAxisAlignment: spaceBetween` redundant (removed).
- **Badges** (`AppBadge`): defensively hardened even though nothing in this
  design system currently places a badge somewhere width-constrained — the
  label is now `Flexible` with `TextOverflow.ellipsis` (not wrap: a badge's
  single-line pill shape is part of its visual identity, so truncating is
  the correct failure mode here, unlike a button's label).
- **List tiles** (`AppListTile`): verified safe as-is — the title/subtitle
  column is already `Expanded`, so `Text` wraps within whatever width the
  row's other content leaves it, rather than overflowing.
- **Cards** (`AppCard`): verified safe as-is — `AppCard` sizes to its
  arbitrary `child`'s content with no fixed-height constraint; there is
  nothing in this component itself that could clip text.
- **Dialogs** (`showAppConfirmationDialog`): verified safe as-is —
  `AlertDialog`'s title/content `Text` wrap naturally in Flutter's own
  layout, and its `actions` row uses Flutter's `OverflowBar`, which stacks
  actions vertically rather than overflowing when they don't fit. The
  `AppButton` fix above additionally protects each individual action.
- **Empty states / error states** (`AppEmptyState`, `AppErrorState`):
  verified safe as-is — title/message `Text` are direct `Column` children
  with `textAlign: center` and no `Row` involved, so they wrap within the
  column's width by Flutter's normal default behavior.

## Nice-to-Haves: implemented vs. deferred

**Implemented** (both naturally fit with low risk):

- `AppButton.expand` renamed to `fullWidth` — `expand` read as ambiguous
  with `Expanded`/`Flexible`'s "grow to fill" behavior; `fullWidth` names
  the actual, unambiguous effect. All four call sites
  (`app_overlays.dart`, `app_states.dart` ×2) and the field's own doc
  comment were updated.
- Speculative `chart4`/`chart5` tokens removed from `AppColors` — two
  colors (a muted teal and plum) invented solely for charts before a
  single chart component exists, exactly the "guess at a shape before a
  real need proves it" pattern this project's own TD-0001 history already
  named as costly. `chartSeries` is now the three colors already derived
  from the semantic palette.

**Deferred, with reasoning disclosed in-code:**

- **Unused `tertiary`/`onTertiary`/`tertiaryContainer`/`onTertiaryContainer`
  fields** were *not* removed from `AppColorScheme`'s `ColorScheme(...)`
  constructor calls. Whether Flutter's `ColorScheme` constructor makes these
  required vs. optional-with-fallback in the Flutter version this code
  targets could not be verified without a Flutter SDK in this sandbox (ADR
  0002). Removing them speculatively risked a build break with no way to
  catch it before a real `flutter analyze` run. Documented as a disclosed,
  deliberate deferral in `app_color_scheme.dart`'s class doc comment, not a
  silent oversight.
- **`VisualDensity.standard` removed**, but this one *was* naturally safe
  to apply — it explicitly restated `ThemeData`'s own default, so removing
  it changes no behavior and was folded into the `AppTheme` edit.
- **Simplifying `AppButton`'s two `switch (variant)` statements** was
  evaluated and left as two, documented inline: one resolves a *widget
  type* and runs after `content` already exists; `_foregroundColor`
  resolves a *color* the loading spinner needs before `content` is built.
  They run at two different points in the method for a real dependency-
  order reason; merging them would relocate the logic, not reduce it.
- **Defensive immutability for `chartSeries`**: `AppSemanticColors.chartSeries`
  is already built from a `const <Color>[...]` literal in `_build()`, which
  Dart treats as a genuinely immutable list at runtime (not just by
  convention) — no further change was needed; this is recorded here as a
  verified-adequate finding, not a silent skip.

## Consequences

**No architectural layer changed.** Every fix in this ADR is a bug fix or a
token addition within the token → theme → component layering ADR 0034
established. `AppOpacity` is a new file at the token layer (the same kind of
addition `app_breakpoints.dart`/`app_motion.dart` already are), not a new
layer; nothing here changes which layer depends on which.

**`warning500`'s hex value changed.** Any place that has ever screenshotted
or visually referenced the old `0xFFC98A2E` will see a barely perceptible
~5% darker amber. No screen currently consumes it (see below), so this has
zero present blast radius; it is recorded here so a future contributor
diffing colors understands why the value moved.

**Still hand-authored, structurally verified — not run in this sandbox.**
Every fix in this ADR inherits ADR 0002's constraint unchanged: no Flutter
SDK exists in this sandbox. The WCAG contrast audit *was* independently,
numerically verified (a real Python implementation of the luminance/contrast
formula, run and its output recorded above) — that part of Important 9 is
genuine, tool-verified evidence, not a claim. Compilation and widget
behavior remain reasoned about by careful API-correctness inspection; see
this phase's own Verification section for exactly what was and was not
executed.

**No screen consumes `AppSemanticColors.warning`/`.success`/`.disabledContent`/
`.focusRing`/`.selected` yet.** Per this project's explicit "no feature
screens" boundary, these tokens exist and are correct but inert — the same
situation `tertiary` was already in, and the same honest disclosure applies:
their first real consumer, once feature screens begin, is the first genuine
test of whether their shape is actually right.
