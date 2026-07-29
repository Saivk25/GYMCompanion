# Gym Companion — mobile

The Flutter client: one app, five tabs (Today, Train, Fuel, Progress, Coach), per
`docs/Gym_Companion_UX_UI_Design_Bible.docx` (repository root).

## Layout

- `lib/shell/` — `app_router.dart` (the `go_router` route table, one `StatefulShellRoute`
  branch per tab) and `app_shell.dart` (the persistent top bar + bottom navigation).
- `lib/features/<tab>/presentation/` — one screen per tab. Currently placeholders; see
  each file's doc comment for which sprint populates it for real.
- `test/` — mirrors `lib/`.

See `docs/adr/0002-flutter-verification-constraint.md` and
`docs/adr/0003-flutter-state-management.md` for two decisions made during this
scaffolding step that weren't already pinned down by the six planning documents.

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

## Status

Sprint 1, Step 3: a five-tab shell that boots and navigates, no real feature data yet.
Domain-driven screens land starting Sprint 2 of the Engineering Master Plan.
