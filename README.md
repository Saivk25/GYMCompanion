# Gym Companion

<!--
CI badge: this repository doesn't have a GitHub remote configured yet
(everything so far has been built and committed locally). Once it's pushed
to GitHub, uncomment the line below and replace OWNER/REPO — GitHub Actions
generates this badge URL automatically from .github/workflows/ci.yml, no
separate setup needed.
[![CI](https://github.com/OWNER/REPO/actions/workflows/ci.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/ci.yml)
-->

A private, AI-assisted fitness operating system — not a workout tracker, not a calorie
counter, not a chatbot. Built first for one user, generalized later only once proven.

This repository is the implementation of the six frozen planning documents in `docs/`.
**Those documents are the source of truth for product and architecture decisions.** This
README only orients you around the code; it does not restate product behavior.

## Reading order (if you are new here)

1. `docs/Gym_Companion_Design_Document.docx` — the personal record this product is built from.
2. `docs/Gym_Companion_System_Architecture.docx` — critical review and technical architecture.
3. `docs/Gym_Companion_Product_Bible.docx` — the complete, prioritized feature catalog.
4. `docs/Gym_Companion_Domain_Model_Decision_Engine_Bible.docx` — entities, workflows, state
   machines, the decision engine, the event system, the rule engines.
5. `docs/Gym_Companion_UX_UI_Design_Bible.docx` — every screen, flow, and interaction.
6. `docs/Gym_Companion_Engineering_Master_Plan.docx` — how the above becomes working software,
   in what order, for a solo developer first.

## Repository layout

| Path | Purpose |
|---|---|
| `apps/mobile/` | The Flutter client — one app, five tabs, per the UX/UI Design Bible. |
| `backend/` | The FastAPI service. `app/domain/` is framework-free business logic; everything else is a thin layer around it. |
| `infra/` | Local development infrastructure (Docker Compose for Postgres + backend). No Kubernetes — see the Engineering Master Plan's over-engineering table for why. |
| `.github/workflows/` | CI only (lint, typecheck, tests, migrations, Docker build, Flutter analyze/test). No deployment workflow exists yet — see the Engineering Master Plan Section 10, release process is manual during MVP through Beta. |
| `docs/` | The six planning documents plus `adr/` for architecture decision records raised during implementation. |
| `scripts/` | One-off developer scripts (database seeding, environment bootstrap, local Postgres, CI-adjacent checks). |
| `tests/e2e/` | Full-stack end-to-end tests spanning the mobile app and backend together. Unit/widget/integration tests live inside `apps/mobile/test/` and `backend/tests/` respectively. |
| `assets/` | Shared design assets referenced by the UX/UI Design Bible (icons, fonts) — not yet populated. |
| `datasets/`, `models/` | Reserved for future use if a custom model is ever justified. Per the Engineering Master Plan, no custom model training is planned for MVP through v1 — these exist so the layout doesn't need to change if that ever becomes justified. |

## Status

Sprint 1 (environment setup) of the Engineering Master Plan is complete: repository
structure, backend and Flutter scaffolds, tooling, testing, linting, formatting, Docker,
Postgres, Alembic, CI, and the framework-independent Domain Core skeleton
(`backend/app/domain/shared_kernel/` — see `backend/README.md`'s "Domain Core" section)
are all done (Steps 1–12). No product-specific business logic exists yet — real
aggregates and the nine rule engines start with Sprint 2. See `docs/adr/` for decisions
made during implementation that weren't already pinned down by
the six planning documents.

## Getting started

- Backend: `backend/README.md`
- Mobile: `apps/mobile/README.md`
- Local Postgres + backend together: `infra/README.md`
