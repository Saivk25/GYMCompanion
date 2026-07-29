"""FastAPI application factory.

Kept deliberately thin: this module wires routers together and does nothing
else. Business logic never lives here — see app/domain/ (framework-free) and
app/api/routes/ (thin HTTP adapters over app/domain/), per the Engineering
Master Plan's Clean Architecture requirement.
"""

from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Gym Companion API",
        version="0.1.0",
        debug=settings.is_local,
    )
    app.include_router(health_router)
    return app


app = create_app()
