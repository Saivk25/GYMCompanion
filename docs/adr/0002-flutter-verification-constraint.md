# ADR 0002: Flutter code is hand-authored and verified structurally, not by running `flutter`

- Status: accepted
- Date: 2026-07-29

## Context

The implementation sandbox used to scaffold this repository has no Flutter SDK
preinstalled, no root/sudo access, and ~3.6 GB of free disk. The Flutter Linux SDK
tarball alone is ~700 MB compressed, the download saturates the sandbox's per-command
time limit (multiple chunked resumes would be needed), and a full first-run artifact
fetch plus Android toolchain would very likely exceed the remaining disk budget. Docker
is also unavailable, ruling out a containerized Flutter image as a workaround.

## Decision

Backend code in this sprint is installed and run for real (a virtualenv outside the
repository, `pytest`, and a live `uvicorn` server hit with `curl` — see Step 2).
Flutter/Dart code is instead:

- Hand-written to exact, current `pubspec.yaml` and Dart syntax conventions.
- Kept deliberately small in this scaffolding step (a five-tab shell with placeholder
  screens, no state wired to real data yet) so there is less surface for an error to
  hide in.
- Verified structurally by this author (dependency versions cross-checked against
  what's known compatible for the declared Flutter/Dart SDK constraint) rather than by
  a passing `flutter analyze` / `flutter test` run.

Real verification — `flutter pub get`, `flutter analyze`, `flutter test`, and
eventually `flutter build` — happens in two places: the CI workflow added in Step 11
(a GitHub-hosted runner has the disk and time budget this sandbox doesn't), and on
Sai's own machine.

## Consequences

The first `flutter pub get` on a real machine or in CI is the true test of this
sprint's Flutter work, not this sandbox's approval. If it fails, that is new
information, not a regression — this ADR exists so that failure is understood as
"the first real check" rather than "something we already verified and broke."

## Update (2026-08-11)

The constraint this ADR describes is resolved: `android`/`ios` platform folders were
generated and committed, and `flutter pub get` / `flutter analyze` / `flutter test` all
ran for real, for the first time, on Sai's own Windows machine. Getting to a clean run
surfaced real information this sandbox's structural verification couldn't have caught —
exactly the outcome this ADR's own Consequences section anticipated:

- 61 pre-existing `flutter analyze` lint issues (unused imports, missing `const`,
  `prefer_conditional_assignment`, one `withOpacity` deprecation).
- 6 real test bugs across three files (a cascading double-`Future.delayed` needing two
  pumps instead of one, an unsupported `ensureVisible(alignment:)` parameter on this SDK
  version, a freshly-pushed route's one-frame `Offstage` "warm-up" state).
- One genuine *application* bug: `active_workout_screen.dart`'s `pushReplacement` to the
  session-summary route was missing `extra: true`, so "Return to Today" never rendered
  after actually ending a session.
- Two further real accessibility bugs, found only once `test/accessibility/
  guideline_test.dart`'s coverage was widened from 2 to 28 of 29 screens
  (`docs/TECH_DEBT.md` TD-0014): Active Workout's Weight/Reps/RPE fields were under the
  design system's 48dp tap-target minimum, and a new guideline test's own pump timing was
  catching a still-transitioning route as a false contrast failure.

Final state: **0 analyzer issues, 303/303 tests passing.** This sandbox still has no
Flutter SDK — the structural-verification discipline this ADR describes remains this
project's working method for any Flutter change made without access to a real machine —
but the standing "never run" caveat that appears throughout this repo's documentation no
longer applies. `flutter run` against a real device/emulator, golden tests, and a real
TalkBack/VoiceOver pass are still outstanding (see `docs/ARCHITECTURE.md` §13).
