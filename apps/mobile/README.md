# Gym Companion — mobile

The Flutter client: one app, five tabs (Today, Train, Fuel, Progress, Coach), per
`docs/Gym_Companion_UX_UI_Design_Bible.docx` (repository root).

## Layout

- `lib/design/` — the design system: `tokens/` (color, typography, spacing, radius,
  elevation, motion, breakpoints, icons — pure values, no widgets), `theme/`
  (assembles tokens into real `ColorScheme`/`TextTheme`/`ThemeData`), `components/`
  (reusable widget primitives — buttons, cards, badges, list tiles, empty/loading/
  error states, bottom sheet and dialog helpers). Import `design/design.dart` from
  any screen rather than individual token/theme/component files. See
  `docs/adr/0034-flutter-design-system.md` (repository root) for the full reasoning
  behind every token and component choice.
- `lib/shell/` — `app_router.dart` (the `go_router` route table, one `StatefulShellRoute`
  branch per tab) and `app_shell.dart` (the persistent top bar + bottom navigation).
  Its `AppBar`/`NavigationBar`/`Chip` inherit the design system automatically through
  `ThemeData`'s component themes — this file itself was not touched by ADR 0034.
- `lib/features/<tab>/presentation/` — one screen per tab. Currently placeholders; see
  each file's doc comment for which sprint populates it for real.
- `test/` — mirrors `lib/`, including `test/design/` for the design system.

See `docs/adr/0002-flutter-verification-constraint.md` and
`docs/adr/0003-flutter-state-management.md` for two decisions made during the
scaffolding step that weren't already pinned down by the six planning documents,
and `docs/adr/0034-flutter-design-system.md` for the design system built on top
of that scaffold.

## First-time setup

This project's Dart/Flutter code was authored without a local Flutter SDK available
(see ADR 0002) — **running `flutter pub get` on a real machine is the first real
verification this code gets**, not a formality:

```bash
cd apps/mobile
flutter pub get
flutter analyze
flutter test
flutter run
```

If `flutter pub get` reports a version conflict, that's expected-possible per ADR 0002
— loosen the offending constraint in `pubspec.yaml` and note the fix in a new ADR.

Platform folders (`android/`, `ios/`) are not yet generated — this scaffold is the Dart
application layer only. Generate them with:

```bash
flutter create --platforms=android,ios --org com.gymcompanion .
```

run from inside `apps/mobile/`. This is safe: it only adds the platform folders when
they don't already exist. If it prompts to overwrite `pubspec.yaml`, `lib/main.dart`,
or `test/`, decline (or restore afterward with `git checkout -- pubspec.yaml lib/main.dart test/`)
— those are already hand-written for this project.

## Testing

```bash
flutter test                       # all widget tests
flutter test --coverage            # writes coverage/lcov.info
```

No separate config file is needed beyond `analysis_options.yaml` (Step 6) — Flutter
discovers `test/**/*_test.dart` by convention. `test/shell/app_shell_test.dart` is the
first test: it verifies the app lands on Today and can navigate to Train via the
bottom bar, and that all five tab destinations render. Mirror `lib/`'s folder
structure under `test/` as features are added, matching the backend's `tests/`
convention.

## Formatting

```bash
dart format .            # apply
dart format --output=none --set-exit-if-changed .   # check only, for CI
```

Dart's formatter is deliberately near-unconfigurable (same philosophy as `gofmt` —
one canonical style, no bikeshedding). This project does not override the default
80-column width: newer Dart SDKs support a `formatter: page_width:` key in
`analysis_options.yaml`, but that key needs a newer SDK floor than this project pins
(`>=3.4.0`), and it isn't worth bumping the floor just to gain a setting that hasn't
been verified in this environment (see ADR 0002). Revisit once on a real machine if
the default width genuinely proves cramped in practice — not before.

## Status

Sprint 1, Steps 3 and 5: a five-tab shell that boots and navigates, with one widget
test, no real feature data yet.

The Flutter Design System (`docs/adr/0034`) is done: tokens, theme architecture
(light + dark), and a closed set of reusable component primitives
(`AppButton`, `AppCard`, `AppBadge`, `AppListTile`, `AppSectionHeader`,
`AppEmptyState`/`AppErrorState`/`AppSkeletonBox`, bottom sheet and confirmation-dialog
helpers) — no `ColorScheme.fromSeed`, no bundled font, no new dependency. `lib/app.dart`
now runs on `AppTheme.light`/`AppTheme.dark` instead of the Step 3 placeholder theme.

An architecture review of that design system was performed and accepted; every
Critical and Important finding it raised has since been resolved (`docs/adr/0035`) —
`AppTheme`/`AppSemanticColors` are memoized, disabled/focus/selection are real named
tokens with a token-driven pressed/hovered/focused interaction system
(`AppOpacity`), touch targets meet 48dp, loading buttons remain screen-reader
accessible, WCAG contrast was computed (not asserted) with two real failures found
and fixed, and typography was audited under large accessibility text sizes across
every named component.

No feature screens, navigation changes, or authentication flow exist yet — per the
brief's own implementation order, this phase stops at the design system.
