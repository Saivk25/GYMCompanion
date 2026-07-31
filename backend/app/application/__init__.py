"""The Application Layer: Sprint 4's orchestration layer, sitting between
the framework-independent Domain Layer (`app.domain`, Sprints 1-3) and
whatever infrastructure eventually implements its interfaces
(`app.infra`, `app.api` — neither depended on from here, ever).

The Application Layer coordinates aggregates, repository interfaces, a
Unit of Work, rule engines, and domain events into complete workflows —
"log this workout," "evaluate today's readiness" — but contains no
business rules of its own. Every decision about whether something is
*allowed* still lives in `app.domain` (an aggregate's own invariants,
or one of the nine-plus rule engines); this layer only decides *in what
order* to call domain code and *what to do with the result*
(persist it, dispatch its events, report success or failure). See
`docs/adr/0022-application-layer-foundation.md` for the full reasoning,
including why this distinction is enforced structurally, not just by
convention.

Only `app.application.shared` exists yet — the foundational interfaces
every future use case builds on. No concrete use case, no repository
implementation, and no framework wiring exists in this layer yet; all
three are explicitly out of scope for this phase.

Depends on nothing outside the Python standard library and
`app.domain` — enforced by the same statically-checked rule
`tests/domain/test_import_boundaries.py` already applies to
`app/domain`, mirrored here by
`tests/application/test_import_boundaries.py`. Never imports
`app.infra`, `app.api`, `app.ai`, or any third-party framework
(FastAPI, SQLAlchemy, Pydantic, ...).
"""
