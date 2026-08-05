"""FastAPI application factory.

Kept deliberately thin: this module wires routers, the lifespan, and
global exception handlers together and contains no business logic of
its own — every request still flows HTTP -> API -> Application Handler
-> Domain -> Persistence, per the Engineering Master Plan's Clean
Architecture requirement and this phase's own stated rules. See
`docs/adr/0031-fastapi-api-layer.md` for the full reasoning behind each
decision below.

**Lifespan**: `app.composition.bootstrap.lifespan()` is a synchronous
`@contextmanager` (this project's I/O is synchronous throughout — see
that module's own docstring). `_lifespan` below is the thin async
wrapper FastAPI's own lifespan protocol requires: it enters the
synchronous context manager, stores the `Container` it yields on
`app.state.container` (the one place `app/api/deps.py`'s
`get_container` reads it from), yields control back to FastAPI for the
life of the process, and lets the synchronous context manager's own
`finally` block run `shutdown()` on the way out.

**Versioning strategy**: a URL path prefix, `/api/v1` — every route
module under `app/api/routes/v1/` is mounted there. Chosen over a
header-based scheme (`Accept: application/vnd.gym.v1+json`) for the
same reason most public HTTP APIs default to it: it's visible in the
URL itself, requires no client-side header plumbing, and is what every
HTTP tool (a browser address bar, `curl`, this project's own OpenAPI
docs UI) shows without extra configuration.

**`debug` is always `False`, in every environment — deliberately not
`settings.is_local`.** Starlette's `ServerErrorMiddleware` only invokes
a registered `Exception` handler (`app/api/errors.py`'s
`_unhandled_exception_handler`, wired up by `register_exception_handlers`
below) when `debug=False`; with `debug=True` it instead returns an HTML
traceback page and re-raises the original exception past the handler
entirely (confirmed empirically — see `tests/api/routes/test_goal_routes.
py`'s malformed-id test, which exercises exactly this path). This
phase's own rule is "global exception mapping" — a `500` must always
come back as the same structured `ErrorResponse` envelope every other
failure does, in local/test the same as anywhere else — so `debug` can't
track environment the way it would in a bare Starlette app. Nothing is
lost for local debugging: `_unhandled_exception_handler` still logs the
full traceback via `logger.exception(...)`, just to the process's own
log output rather than the HTTP response body.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.errors import register_exception_handlers
from app.api.routes.health import router as health_router
from app.api.routes.v1.goal import router as goal_router
from app.api.routes.v1.nutrition import router as nutrition_router
from app.api.routes.v1.progress import router as progress_router
from app.api.routes.v1.readiness import router as readiness_router
from app.api.routes.v1.workout import router as workout_router
from app.composition.bootstrap import lifespan as composition_lifespan
from app.core.config import get_settings


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    with composition_lifespan() as container:
        app.state.container = container
        yield


def create_app() -> FastAPI:
    get_settings()  # validated once, eagerly, so a bad .env fails at startup, not on first request
    app = FastAPI(
        title="Gym Companion API",
        version="0.1.0",
        description=(
            "HTTP surface over the Gym Companion Application Layer — a thin "
            "adapter with no business logic of its own. See docs/adr/0031-"
            "fastapi-api-layer.md."
        ),
        debug=False,  # see the module docstring for why this is never settings.is_local
        lifespan=_lifespan,
    )
    register_exception_handlers(app)

    app.include_router(health_router)
    app.include_router(goal_router, prefix="/api/v1")
    app.include_router(nutrition_router, prefix="/api/v1")
    app.include_router(progress_router, prefix="/api/v1")
    app.include_router(readiness_router, prefix="/api/v1")
    app.include_router(workout_router, prefix="/api/v1")

    return app


app = create_app()
