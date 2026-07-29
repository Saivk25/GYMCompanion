# Infra — local development

`docker-compose.yml` runs Postgres and the backend together for local development.
No orchestration platform beyond Compose — see the Engineering Master Plan's
"what we are deliberately not building yet" table (Section 1) for why Kubernetes
isn't here and won't be for a long time.

```bash
cd infra
docker compose up --build
```

This starts Postgres on `localhost:5432` (user/password/db all `gymcompanion` — local
development only, never used outside `GYM_ENVIRONMENT=local`) and the backend on
`localhost:8000`, waiting for Postgres's healthcheck before starting the backend.

Verify it's up:

```bash
curl http://localhost:8000/health
```

Apply database migrations (not run automatically — see the comment in
`docker-compose.yml`):

```bash
docker compose exec backend alembic upgrade head
```

## Status and a verification note

Not yet run in this environment — the implementation sandbox this project was
scaffolded in has no Docker available (see `docs/adr/0004-docker-verification-constraint.md`).
The Dockerfile and this Compose file were written and reviewed for correctness (the
Compose YAML is schema-validated; the Dockerfile follows a conventional, minimal
multi-stage-free pattern deliberately kept simple because `psycopg[binary]` needs no
compiler toolchain), but `docker compose up` on a real machine is this configuration's
first real test, not a formality.

