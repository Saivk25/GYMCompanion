# Release process

## Current status

**No version of this project has been released.** `backend/pyproject.toml` and
`apps/mobile/pubspec.yaml` both currently read `0.1.0`, no Git tag exists, and there is no
GitHub remote configured for this repository yet. This document describes the process that
*will* apply once a release is cut — it is written now, ahead of the first release, so the
process is decided deliberately rather than improvised under pressure the first time it
matters.

## Versioning: Semantic Versioning

This project follows [SemVer 2.0.0](https://semver.org/): `MAJOR.MINOR.PATCH`.

- **MAJOR** — a breaking change to the backend's public API contract (`backend/app/api/`) or a
  change that requires a fresh mobile-app install/data reset. Given the backend has no external
  API consumers yet, expect this to stay `0` for a long time.
- **MINOR** — a new feature that doesn't break existing API consumers or force a mobile
  reinstall (a new endpoint, a new screen, a new rule engine).
- **PATCH** — a bug fix, a documentation fix, or an internal refactor with no behavior change.

**Pre-1.0 note:** per SemVer's own spec, anything under `1.0.0` is explicitly allowed to change
in breaking ways between minor versions — this project will stay in the `0.x` range until the
backend API and the mobile client's real-device behavior have both been validated end to end
(see `docs/adr/0054`'s release checklist and `docs/ARCHITECTURE.md`'s "known limitations"). Two
independent version numbers exist today (`backend/pyproject.toml`'s and
`apps/mobile/pubspec.yaml`'s) because the backend and the mobile client are deployed
independently; they are not required to match, though they currently do by coincidence
(both `0.1.0`).

## What blocks the first tagged release

Per `docs/adr/0054-testing-and-release-readiness.md`'s own release checklist (still accurate as
of `docs/adr/0055`):

1. A real Flutter SDK run (`flutter analyze` / `flutter test`) — every line of Flutter code in
   this repository has been hand-authored and statically verified, never executed
   (`docs/adr/0002`).
2. `android`/`ios` platform folders (`flutter create --platforms=android,ios .` against the
   existing `apps/mobile/lib/`) — do not exist yet.
3. A real device/TalkBack/VoiceOver accessibility pass, beyond the static audit in
   `docs/adr/0053`.
4. App icon, splash screen, and app-store metadata.
5. A real backend deployment target (currently: none — see `SECURITY.md`).

None of these is a design gap — each is explicitly named as pending, environment-dependent work
in the ADRs above.

## GitHub Releases strategy

Once the checklist above is clear:

1. Update the version in `backend/pyproject.toml` and/or `apps/mobile/pubspec.yaml` (whichever
   component actually changed since the last release — they can diverge, e.g. `backend@0.3.0`
   with `mobile@0.2.1`).
2. Move the relevant `[Unreleased]` entries in `CHANGELOG.md` under a new `## [X.Y.Z] -
   YYYY-MM-DD` heading.
3. Tag the release: `git tag -a vX.Y.Z -m "vX.Y.Z"` (mobile) or `backend-vX.Y.Z` if backend and
   mobile ever need independently taggable histories — not needed yet, since both live in one
   repository and have released together so far.
4. Push the tag: `git push origin vX.Y.Z`.
5. The `.github/workflows/release.yml` workflow (see that file) runs on tag push: it builds the
   backend Docker image and drafts a GitHub Release with the corresponding `CHANGELOG.md`
   section as the release notes. It does **not** deploy anywhere or publish a mobile build to an
   app store — those steps remain manual until a real deployment target and app-store account
   exist, consistent with `docs/adr/0004` and `docs/adr/0054`'s own scope.
6. Publish the drafted GitHub Release once the generated notes are reviewed.

## Branching model

`master` is always releasable — there is no long-lived `develop` branch. Feature work happens on
short-lived branches merged back into `master` via pull request (see `CONTRIBUTING.md`). This is
a deliberately simple model appropriate for a single-maintainer, pre-1.0 project; a
release-branch model (`release/X.Y`) is not needed until multiple release lines must be
patched concurrently.
