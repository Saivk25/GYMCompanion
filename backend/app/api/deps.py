"""FastAPI dependency wiring — the one place any route reaches into the
Composition Root.

Two dependencies every route in `app/api/routes/v1/` uses:

- `get_container` reads the process-lifetime `Container` FastAPI's own
  `lifespan` (`app/main.py`) built once at startup and stored on
  `app.state.container`.
- `handler_dependency(handler_type)` is a factory returning a
  per-request FastAPI dependency that resolves a fresh instance of
  exactly the one handler type a given route needs — "fresh", not
  cached, because `Container.handler()` itself is designed to never be
  cached (see that method's own docstring): each call also constructs a
  brand-new `SqlAlchemyUnitOfWork`, which is what gives every request
  its own request-scoped `UnitOfWork` with no risk of two concurrent
  requests racing on a shared session.

No route ever imports `app.composition.Container` and calls
`.handler()` itself — routing every handler resolution through this one
module is what keeps "dependency injection everywhere" (this phase's
own rule) enforceable by a single import-boundary test
(`tests/api/test_import_boundaries.py`) rather than by convention alone.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

from fastapi import Depends, Request

from app.application.shared.interfaces import Handler
from app.composition.container import Container

H = TypeVar("H", bound=Handler[Any, Any])


def get_container(request: Request) -> Container:
    """Returns the `Container` FastAPI's lifespan built once at process
    startup. Never constructs one itself — `Container.validate()` (run
    once, inside `bootstrap()`) exercises the whole dependency graph, so
    a `Container` is meant to be built exactly once per process, not
    once per request.
    """
    container: Container = request.app.state.container
    return container


def handler_dependency(handler_type: type[H]) -> Callable[[Container], H]:
    """Builds a FastAPI dependency that resolves a fresh `handler_type`
    instance via the request-scoped `Container`, on every request.

    Usage, in a route module: `_get_create_goal_handler =
    handler_dependency(CreateGoalHandler)`, then `handler:
    CreateGoalHandler = Depends(_get_create_goal_handler)` as a route
    parameter — the same shape every route in this API uses to obtain
    its one handler, with no per-route boilerplate beyond naming the
    handler type.
    """

    def _resolve(container: Container = Depends(get_container)) -> H:  # noqa: B008 — FastAPI's own DI pattern
        return container.handler(handler_type)

    return _resolve
