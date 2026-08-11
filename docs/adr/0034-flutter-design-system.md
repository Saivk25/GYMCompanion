# ADR 0034: Flutter Design System — hand-tuned tokens over `colorSchemeSeed`, native system fonts over a bundled typeface, ripple disabled, and a closed component allow-list

- Status: accepted
- Date: 2026-08-06

## Context

Sprint 1 (Step 3) scaffolded a five-tab Flutter shell with a placeholder
theme (`ThemeData(useMaterial3: true, colorSchemeSeed: const
Color(0xFF1F2937))`) — deliberately minimal, since that step's own scope
was "does the app boot and navigate," not visual identity (see ADR 0002).
The backend is now frozen and accepted; this phase begins the production
Flutter frontend, under an explicit, unusually detailed brief: the app
must not read as AI-generated, template-derived, or "a Material demo" on
any screen, and every visual decision must be justified rather than
defaulted into. Per that brief's own stated implementation order, this
phase builds *only* the design system — tokens, theme architecture, and a
small set of reusable component primitives — and explicitly does not
begin feature screens, navigation architecture, or the authentication
flow, all of which come later in that order.

The brief names a specific failure mode to avoid: reaching for whatever a
Flutter template or an AI assistant would reach for by default
(`ColorScheme.fromSeed`, a bundled Google Font, Material's default ripple
and shadow, oversized rounded corners) rather than a considered choice.
Every decision below states what was rejected and why, not only what was
chosen — the "why not" is the actual content of a design system that is
trying not to look generated.

## Decision

### 1. Hand-authored, structurally verified — not run in this sandbox

This phase inherits ADR 0002's constraint unchanged: no Flutter SDK is
available in this implementation sandbox. Every file in `lib/design/` was
written to exact, current Dart 3 / Flutter 3.24+ syntax and cross-checked
against long-stable, well-documented Flutter APIs; genuinely uncertain
API surface was avoided in favor of the version most likely to be correct
on the CI runner's `stable` channel and on a real developer machine today
(see the "Known verification risk" note in Consequences for the one area
this could not be fully de-risked by inspection alone). `flutter pub get`
/ `flutter analyze` / `flutter test`, run in CI and on Sai's own machine,
remain the true first verification, exactly as ADR 0002 already
established for all prior Flutter work.

### 2. Tokens are hand-selected, not `ColorScheme.fromSeed` / `colorSchemeSeed`

`ColorScheme.fromSeed` is Material's own algorithmic tonal-palette
generator — correct and accessible for *any* input color, which is
exactly why using it produces a palette that could belong to any app that
also used it. The placeholder theme this phase replaces used exactly this
shortcut, appropriately for a scaffolding step; keeping it into
production would have been the single fastest way to fail this phase's
own brief. `lib/design/tokens/app_colors.dart` instead defines every
color by hand: one reused neutral ("slate") ramp read in opposite
directions by each theme (the same technique GitHub Primer, Stripe, and
Linear use — not a Material default, a deliberately studied one), one
restrained accent ("signal," a muted confident blue) reserved for primary
actions only, and calm success/warning/danger tones explicitly tuned away
from saturated "alert" colors per the UX/UI Design Bible's own rejection
of "alarm-red overuse" and red/green pass-fail body-metric framing
(Sections 11, 18). `lib/design/theme/app_color_scheme.dart` assembles
these into full light/dark `ColorScheme`s via the base `ColorScheme(...)`
constructor field-by-field — not `.light()`/`.dark()` with only a few
overrides — so every token this app's identity depends on is a reviewed
decision, not an inherited Material default.

### 3. Typography: five Bible-named levels mapped onto Flutter's own `TextTheme`, no bundled font

The UX/UI Design Bible (Section 10) specifies exactly five named levels —
Display, Title, Heading, Body, Caption — and, deliberately, no pixel
values. Flutter's Material 3 `TextTheme` already has five families at
three sizes each (display/headline/title/body/label) — the same
five-level hierarchy under different names, not a coincidence, since both
converge on the same standard typographic convention. Rather than
inventing a second, parallel naming scheme that would shadow Flutter's
own (and be silently wrong the moment a third-party widget reads
`Theme.of(context).textTheme` directly), `lib/design/tokens/
app_typography.dart` builds real `TextTheme` values under Flutter's own
names, with `AppTypography.heading`/`.title`/`.body`/`.caption`/`.display`
as a thin, optional alias layer for call sites that prefer the Bible's
vocabulary — never a second source of truth.

No custom font is bundled. Apple Health, Apple Fitness, Things 3, and
Craft — the products this system studies for craftsmanship — build their
entire typographic identity on the platform's own system font, executed
with real discipline in size/weight/spacing, not on a licensed or
Google-Fonts typeface. Reaching for a Google Font (Inter, Poppins, and
similar) was considered and rejected as exactly the reflexive first move
a template or an AI assistant makes. `app_typography.dart` instead
resolves `.SF Pro Display`/`.SF Pro Text` (Flutter/Skia's documented
dot-prefixed aliases for "the current iOS/macOS system font," evaluated
via `defaultTargetPlatform`, not `dart:io`, so the choice is testable and
platform-correct) on iOS/macOS, and Flutter's bundled Roboto (via
`fontFamily: null`) everywhere else — genuinely native per platform, zero
licensing cost, zero bundle-size cost, and a considered decision to
revisit only with real typeface specimens in hand, not a placeholder.

Numbers that change in place (a rep counter, a live timer) use
`AppTypography.tabular()`, which applies `FontFeature.tabularFigures()` —
implementing the Bible's own "fixed-width figure treatment... so they
don't jitter when they change" as a real, reusable helper rather than a
one-off `copyWith` a screen author has to remember.

### 4. Spacing: a ten-step, 4px-grid scale extending the Bible's illustrative values

The Bible's own spacing rule (Section 10) is structural only — "a single
8-point-based scale (4/8/16/24/32/48); no arbitrary spacing values
anywhere" — and explicitly specifies no complete numeric scale, since
that document deliberately stops short of pixel values. `lib/design/
tokens/app_spacing.dart` completes it: `4, 8, 12, 16, 20, 24, 32, 40, 48,
64`, every value still a multiple of 4, with `12`/`20`/`40`/`64` as the
natural interpolations needed for a full, usable scale. This is a
refinement of the Bible's rule, not a deviation from it.

### 5. Radius: restrained, with fully-rounded shapes reserved for genuine pills

Oversized rounded corners (20-32px "bubble" cards) were identified as one
of the fastest, easiest-to-spot signals of unstyled or generated Flutter
UI — the visual flourish requiring the least design judgment to reach
for. `lib/design/tokens/app_radius.dart` caps structural containers at
4-16px (`xs`-`lg`) and reserves a large fixed `full` value strictly for
genuinely circular/pill shapes (chips, small avatars, toggle tracks) —
never for anything a user would call "a card." `AppCard` uses `md` (12px)
exclusively; there is no larger radius option a screen could reach for
instead.

### 6. Elevation: exactly three tiers, soft custom shadows, dark-mode surface tint instead of shadow

The Bible (Section 10) specifies exactly three elevation meanings — flat,
raised card, overlay — rejecting Material's own six-plus discrete
elevation levels as unnecessary variation. `lib/design/tokens/
app_elevation.dart` implements exactly those three as an enum, with two
outputs per tier: a numeric `elevation` for genuine `Material`-family
widgets, and a hand-tuned `List<BoxShadow>` (low-opacity, large-blur,
small-offset — the "soft shadow" technique Linear, Notion, and Stripe
Dashboard use) for `AppCard` and other custom containers, deliberately
not Flutter's own `Card` shadow, which is tighter, more opaque, and one
of the most recognizable "Material demo" tells.

Dark mode does not rely on shadow at all for its primary elevation
signal — a shadow barely registers against a near-black canvas, so the
physical metaphor breaks down exactly where digital products often stop
thinking about it. `app_color_scheme.dart`'s `AppColorScheme.surfaceAt`
instead lightens a raised surface's fill by lerping toward
`surfaceContainerHighest`, the same "raised surfaces get lighter" dark-
theme convention Material 3's own guidance establishes, implemented with
hand-controlled math rather than left to a framework default.

### 7. `AppSemanticColors`: one new `ThemeExtension`, extending `ColorScheme` rather than duplicating it

Material 3's `ColorScheme` already provides a complete semantic system —
primary/secondary/tertiary/error and their container/`on*` pairs. This
design system reuses it directly: `danger` *is* `ColorScheme.error`,
never a second, parallel token that could silently drift out of sync with
it. What `ColorScheme` has no concept of is **success** and **warning** —
states this app needs constantly (a completed session, a reduced-capacity
readiness band) that are neither "the brand color" nor "an error."
`lib/design/theme/app_semantic_colors.dart` is exactly one `ThemeExtension`
adding those two, plus an ordered qualitative chart-series palette and a
neutral chart-reference-line color, following `ColorScheme`'s own
container/`on*` pattern so it is immediately familiar to anyone who
already knows `colorScheme.primaryContainer`. This is the one new
abstraction this phase introduces beyond the token/theme layer itself,
and it exists because Flutter's own semantic system has a real, specific
gap, not because inventing a parallel color system seemed convenient.

### 8. Icons: Flutter's bundled Material Icons only, outline-default / filled-selected, a curated allow-list

No new icon package or bundled font. Flutter ships the classic Material
Icons font in the framework itself; pulling in the newer "Material
Symbols" family (via a pub package) for a marginally more contemporary
glyph style was considered and rejected as an unverifiable dependency for
a difference few users would consciously notice. `lib/design/tokens/
app_icons.dart` is a curated allow-list — `AppIcons.today`, never
`Icons.today_outlined` reached into directly from a screen — reusing the
exact glyphs `lib/shell/app_shell.dart`'s existing bottom navigation
already established (outline for inactive, filled for selected, a
functional state signal, not decoration) rather than picking new ones.
Icons with no meaningful outline/filled distinction (arrows, chevrons,
a plus sign) use their one canonical glyph rather than forcing a style
suffix that would not change how the icon renders — a deliberate,
disclosed judgment call made to keep every icon reference in this file
high-confidence against Flutter's actual bundled icon set (see
Consequences).

### 9. Motion: short, decelerating, never bouncy; a reduced-motion-aware helper

`lib/design/tokens/app_motion.dart` caps every duration at 320ms — the
products studied for craftsmanship (Linear, Arc) are notably *fast*, and
a slower "cinematic" transition reads as latency, not polish, once a
user performs the same interaction repeatedly, which describes nearly
every interaction in a daily-use fitness app. Every curve decelerates
into its final state; no bounce/spring/elastic curve exists anywhere in
this token set, since an overshoot reads as playful/gamified — directly
opposed to the Bible's explicit rejection of "gaming dashboard"
aesthetics. `AppMotion.resolve(context, duration)` returns `Duration.zero`
when the OS reduced-motion accessibility setting is on, implemented as a
real helper rather than a convention every animated widget has to
remember — `AppSkeletonBox`'s pulse is the one component in this phase
that actually calls it, and every future animated component should route
through it the same way.

### 10. Breakpoints: Material 3's own published window-size-class boundaries, not invented numbers

`lib/design/tokens/app_breakpoints.dart` uses 600/840 — Material 3's own
documented compact/medium/expanded boundaries, not round numbers chosen
for this app. Reusing an externally validated standard means the scale is
already checked against real device sizes, and matches what a future
contributor researching "Flutter breakpoints" already expects. `expanded`
exists today even though no screen in this phase branches on it yet — the
UX/UI Design Bible (Section 17) scopes desktop out of MVP but names a
tablet master-detail pattern for Progress and Coach specifically; the
boundary is free to define now and costly to retrofit later.

### 11. Ripple disabled app-wide; feedback comes from each component's own state

Material's default ink-ripple touch feedback is one of the most
immediately recognizable "this is a Material demo" signals — supplied by
Android by default, not a considered choice. `AppTheme` sets
`splashFactory: NoSplash.splashFactory` and `highlightColor:
Colors.transparent` globally; touch feedback instead comes from each
component's own subtle state change (an `InkWell` still participates in
hover/focus/pressed states even with splash disabled, and future
components should lean on `WidgetStateProperty`-driven opacity/tone
shifts rather than reintroducing ripple locally).

### 12. A closed set of component primitives, not a general-purpose UI kit

This phase builds exactly the primitives the Bible's own Section 10 table
names as needing "one shared component library across all five tabs":
`AppButton` (the Bible's exact button hierarchy — primary/secondary/
tertiary/destructive, never a raw `ElevatedButton` reached into
directly), `AppCard` (the one card container), `AppBadge` (color always
paired with icon and label — never color alone, a direct, structural
implementation of "color-independent communication," not just a
convention), `AppListTile` (one row shape for every list, per the Bible's
explicit "a meal row and a session-history row share the same underlying
list-row component"), `AppSectionHeader`, and the three required states
— `AppEmptyState`, `AppErrorState` (always paired with retry), and
`AppSkeletonBox`/`AppLoadingIndicator` (skeleton for predictable layouts,
a spinner reserved for genuinely short indeterminate waits only, per the
Bible's own distinction). `showAppBottomSheet`/`showAppConfirmationDialog`
implement the Bible's "bottom sheets by default, full-screen dialogs only
for genuinely irreversible actions" rule as the two sanctioned overlay
entry points. Nothing beyond this set was built — feature screens (Step
13 of the brief's own implementation order) will surface real gaps in
this list; inventing components speculatively ahead of a real call site
was avoided, the same "no speculative abstraction" discipline the
backend's own TD-0001 history already established for this project.

### 13. Folder structure

```text
lib/design/
  tokens/       — pure values only (color, type, spacing, radius,
                   elevation, motion, breakpoints, icons). No widgets.
  theme/        — assembles tokens into real Flutter Theme objects
                   (ColorScheme, TextTheme, ThemeExtension, ThemeData).
  components/   — reusable widget primitives built on tokens + theme.
  design.dart   — single barrel export; every screen imports this one
                   file, never individual token/theme/component files.
```

Mirrors the backend's own layered-package convention (`app/domain/`,
`app/application/`, ...) applied to a design system's own natural layers
— values, then theme assembly, then components — each layer depending
only on the one below it, never sideways or upward. `test/design/`
mirrors this structure, per the existing `test/` convention.

## Consequences

**Nothing in this phase depends on a new package.** `pubspec.yaml` is
unchanged — every decision above uses only what Flutter's SDK already
ships. This was a deliberate constraint, not an accident: a design system
built from a bundled font or an icon package would add real, uninspect-
able dependency risk in a sandbox with no Flutter SDK to verify a `pub
get` against (ADR 0002).

**Known verification risk, disclosed rather than hidden.** Several
`ThemeData` sub-theme class names (`CardThemeData`, `DialogThemeData`,
and similar) underwent a Flutter-wide rename from an older `XxxTheme`
naming scheme; this file uses the renamed classes on the judgment that,
on today's actual Flutter `stable` channel, that rename has long since
completed. If a real `flutter analyze` run against an unusually old pinned
SDK reports these names as unresolved, that is new information about
exactly which SDK is in use, not a design regression — the fix is a
class-name swap in `app_theme.dart` alone, not a re-architecture. This is
named explicitly so a failure here is understood the way ADR 0002 already
asks every Flutter verification failure in this project to be understood.

**`lib/shell/app_shell.dart` was deliberately not touched.** Its `AppBar`,
`NavigationBar`, and `Chip` automatically inherit this phase's styling
through `ThemeData`'s component themes with zero code changes there —
proof the theme layer is doing its job, and confirmation that navigation
architecture (Step 11 of the brief's own order) remains genuinely
untouched, not implicitly started early.

**No feature screens, navigation changes, or authentication flow exist
yet.** Per the brief's explicit instruction, this phase stops here.
`AppEmptyState`/`AppErrorState`/`AppSkeletonBox` are proven only by the
smoke tests in `test/design/design_system_test.dart` pumping them in
isolation — real screens will be the first true test of whether this
component set is actually sufficient, the same "first real check, not a
regression if it needs a small addition" posture ADR 2 and this ADR's own
first Consequence both take toward Flutter verification generally.

**`AppSemanticColors` is the one new abstraction this phase introduces.**
Every other decision above is a token or a `ThemeData` field Flutter
already defines the shape of. This was a deliberate outcome, not an
oversight: the brief's own self-review question ("did a decision feel
trendy instead of timeless") was applied to abstraction choices too, not
only to color and shape — a design system with many bespoke abstractions
before a single real screen has used them would itself be the kind of
over-engineering this project's backend history (TD-0001, TD-0002) has
already shown costs more to carry than to add later, once a genuine
second need proves it.
