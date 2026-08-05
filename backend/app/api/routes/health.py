"""Health, liveness, and readiness endpoints.

`/health` (unchanged from its own original docstring) and `/health/live`
(an explicit, identically-behaved alias — added so a caller that already
expects a `/live` path by Kubernetes-style convention finds one) both
deliberately have no dependency on the database or any other module: a
liveness check that can fail because the database is briefly unavailable
is not distinguishing "the process is alive" from "a dependency is
degraded".

`/health/ready` is the separate check that *does* depend on the
database — added in this phase, now that there is a `Container` (and
therefore a real `Engine`) to be ready against. It calls
`Container.is_database_ready()`, not a `Repository`/`UnitOfWork`: a
readiness probe's only question is "can this process reach its
database," a pure infrastructure fact with no domain meaning, the same
reason a Kubernetes readiness probe is conventionally a raw connectivity
check, not a request that flows through application code. Delegating
the actual connectivity check to `Container` (rather than reaching for
`sqlalchemy` directly here) also keeps this module — and every other
module in `app/api` — free of any direct SQLAlchemy import, which is
what lets `tests/api/test_import_boundaries.py` forbid `sqlalchemy`
across this whole package with no per-file exception.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_container
from app.composition.container import Container

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/live")
def liveness() -> dict[str, str]:
    """An explicit `/live` alias for `/health` — see the module
    docstring for why both share the exact same "no dependencies"
    behavior."""
    return {"status": "ok"}


@router.get("/health/ready")
def readiness(container: Container = Depends(get_container)) -> dict[str, str]:
    """Ready means "can open a connection and run a trivial query
    against the database this process was configured with" — nothing
    more. A failure here maps to 503, not the generic 500 an unhandled
    exception would produce, so a caller (e.g. an orchestrator deciding
    whether to route traffic here) can distinguish "this instance isn't
    ready yet" from "this instance is broken."
    """
    if not container.is_database_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="database unavailable",
        )
    return {"status": "ready"}
