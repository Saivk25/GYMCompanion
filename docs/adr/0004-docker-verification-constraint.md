# ADR 0004: Docker/Compose files are reviewed, not executed, in this environment

- Status: accepted
- Date: 2026-07-29

## Context

Same underlying constraint as ADR 0002 (Flutter), applied to Docker: the
implementation sandbox used to scaffold this repository has no `docker` binary
available and no path to install one (no root, and Docker-in-Docker typically needs
privileges this sandbox doesn't grant).

## Decision

`backend/Dockerfile` and `infra/docker-compose.yml` are hand-written to conventional,
correct syntax and reviewed carefully:

- The Compose file is parsed and schema-checked with a YAML parser (structurally
  valid; this does not catch every possible Compose-specific semantic error, but
  catches syntax mistakes).
- The Dockerfile deliberately avoids anything exotic — a single-stage build, no
  compiler toolchain (justified by the choice of `psycopg[binary]` over `psycopg`
  in `backend/pyproject.toml`, which ships its own libpq) — specifically to
  minimize the surface area that could be wrong without a build to catch it.

Real verification — `docker compose up --build`, confirming the backend actually
reaches Postgres and serves `/health` — happens on a real machine or in CI (Sprint
1, Step 11, which runs the backend's test suite against a real Postgres service
container; a full `docker compose` smoke test is a reasonable CI addition beyond
Step 11's scope, worth revisiting once this stack is verified once for real).

## Consequences

Treat the first `docker compose up --build` as new information. If the backend
image fails to build or can't reach Postgres, that's this configuration's first
real test failing, not a regression against something previously working.
