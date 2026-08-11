## Summary

<!-- What does this PR do, and why? One or two sentences. -->

## Related issue

Closes #

## Type of change

- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing behavior to change)
- [ ] Documentation only
- [ ] Refactor (no behavior change)
- [ ] CI / tooling

## Which part(s) of the repo does this touch?

- [ ] `backend/` (FastAPI service)
- [ ] `apps/mobile/` (Flutter client)
- [ ] `docs/` (ADRs, architecture, planning docs)
- [ ] CI / GitHub configuration

## Checklist

- [ ] I read `CONTRIBUTING.md`.
- [ ] I followed the existing Clean Architecture layering (domain never depends on
      infrastructure/framework code).
- [ ] Tests were added or updated (`pytest` for backend, `flutter test` for mobile), or this
      change genuinely doesn't need one (explain below).
- [ ] `make backend-lint backend-typecheck backend-test` passes locally (backend changes).
- [ ] `flutter analyze` and `flutter test` pass locally (mobile changes) — see
      `docs/adr/0002` if you're working from an environment without the Flutter SDK.
- [ ] I added an ADR (`docs/adr/`) if this makes a non-obvious architectural decision.
- [ ] I updated `docs/TECH_DEBT.md` if this resolves or introduces a tracked trade-off.
- [ ] I updated relevant docs (`README.md`, `docs/ARCHITECTURE.md`, module `README.md`s) if
      behavior changed.

## Screenshots / recordings (mobile UI changes only)

<!-- Before/after, if this touches a screen. Delete this section otherwise. -->

## Notes for reviewers

<!-- Anything that isn't obvious from the diff — trade-offs considered, things you're unsure
about, follow-up work you're deliberately deferring. -->
