"""Health check endpoint.

Deliberately has no dependency on the database or any other module: a health
check that can fail because the database is briefly unavailable is not
distinguishing "the process is alive" from "a dependency is degraded". A
separate readiness check is added once there is a database to be ready against
(Sprint 1, Step 10).
"""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
