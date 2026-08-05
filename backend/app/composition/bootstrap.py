"""Application bootstrap and shutdown — the two functions that make this
codebase an actually-runnable process, independent of any web framework.

`bootstrap()` is what "the application is executable without HTTP
endpoints yet" (this phase's own stated goal) means concretely: run it
and you get back a fully-wired, fully-validated `Container` — every
repository factory proven to construct the right type, every rule engine
constructed, every one of the ~43 handlers proven resolvable — with
nothing left implicit or deferred to "whenever the first request happens
to touch it." A future FastAPI app wires this in as its own `lifespan`
context manager (an async wrapper around `lifespan()` below, since
FastAPI's own lifespan protocol is async and this project's I/O is
synchronous throughout — `app/domain/shared_kernel/repository.py`'s own
docstring already gives the reason: "the infra layer this will be
implemented against is already sync"); that wrapper is the future API
Layer phase's job, not this one's — `app/main.py` is deliberately left
untouched by this phase (see `docs/adr/0030-composition-root.md`).
"""

from __future__ import annotations

import logging
from collections.abc import Generator
from contextlib import contextmanager

from app.composition.container import Container, build_container
from app.composition.logging_config import configure_logging
from app.core.config import Settings, get_settings
from app.infra.database import build_engine

logger = logging.getLogger(__name__)


def bootstrap(settings: Settings | None = None) -> Container:
    """Starts up: configures logging, builds the database engine,
    assembles the `Container`, and validates the whole dependency graph
    before returning it — a caller never receives a `Container` that
    `validate()` would have rejected. Raises `app.composition.container.
    CompositionError` if validation fails; does not catch or soften that
    failure, since a broken composition root should stop the process from
    starting, not degrade silently.

    `settings` is accepted explicitly (defaulting to `get_settings()`,
    the process-wide cached instance) so a test can bootstrap against an
    independent `Settings` object — e.g. one pointed at a different
    `database_url` — without needing to mutate environment variables or
    the `lru_cache`d singleton.
    """
    resolved_settings = settings if settings is not None else get_settings()
    configure_logging(resolved_settings)
    engine = build_engine(resolved_settings.database_url)
    container = build_container(resolved_settings, engine)
    container.validate()
    logger.info(
        "application bootstrap complete (environment=%s)",
        resolved_settings.environment,
    )
    return container


def shutdown(container: Container) -> None:
    """Shuts down: disposes the `Container`'s database engine, releasing
    every pooled connection. The counterpart to `bootstrap()` — every
    successful `bootstrap()` call is expected to have a matching
    `shutdown()` call once the process (or a test) is done with the
    `Container` it returned, the same paired-resource discipline
    `contextmanager`-based `lifespan()` below exists to guarantee
    automatically.
    """
    logger.info("application shutdown starting")
    container.engine.dispose()
    logger.info("application shutdown complete")


@contextmanager
def lifespan(settings: Settings | None = None) -> Generator[Container, None, None]:
    """`bootstrap()`/`shutdown()`, paired: `with lifespan() as container:`
    guarantees `shutdown()` runs even if the body raises — the same
    always-clean-up-on-exit guarantee every other context manager in this
    codebase provides (e.g. `UnitOfWork.__enter__`/`__exit__`,
    `app/infra/database.py`'s `tenant_scope`). Framework-agnostic on
    purpose: a future FastAPI `lifespan` is a thin async function that
    enters this synchronous context manager and yields, not a
    reimplementation of it.
    """
    container = bootstrap(settings)
    try:
        yield container
    finally:
        shutdown(container)
