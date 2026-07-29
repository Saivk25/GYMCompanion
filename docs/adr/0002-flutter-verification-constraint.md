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
