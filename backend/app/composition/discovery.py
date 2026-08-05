"""`discover_handler_types()`: finds every concrete `CommandHandler`/
`QueryHandler` subclass under `app.application`, by walking the package
and inspecting each module — not by maintaining a hand-written list.

**Why discovery instead of a registration table.** Every handler this
codebase already has (43, across eight aggregates — see `docs/adr/0030-
composition-root.md`) follows exactly one of three constructor shapes:
`uow` only, `uow` + `dispatcher`, or `uow` + `dispatcher` + `clock` (see
`Container.handler()`, which resolves any of the three generically via
`inspect.signature`). A hand-maintained `tuple[type[Handler[Any, Any]],
...]` naming all 43 would carry the same information `inspect.signature`
already recovers from each class directly, with a real cost a generic
approach doesn't have: it goes stale silently the moment a 44th handler
is added and nobody remembers to add its row here too — exactly the kind
of drift `tests/composition/test_dependency_graph.py`'s "every handler
can resolve its dependencies" check exists to catch, which a stale table
would silently stop doing. Walking the package instead means a new
handler is included automatically, the day it's added, with no second
place to update.

This intentionally does not use any of `app.application`'s own runtime
behavior — it only imports modules and inspects classes with `inspect`,
never calls `handle()` or constructs anything — so it stays a pure
discovery step, safe to run from `Container.validate()` at application
startup with no side effects of its own.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from typing import Any

import app.application
from app.application.shared.command_handler import CommandHandler
from app.application.shared.interfaces import Handler
from app.application.shared.query_handler import QueryHandler

_ABSTRACT_HANDLER_TYPES = (Handler, CommandHandler, QueryHandler)


def discover_handler_types() -> tuple[type[Handler[Any, Any]], ...]:
    """Every concrete (non-abstract) `Handler` subclass reachable by
    importing every module under `app.application`, in a fixed
    (sorted-by-qualified-name) order so the result — and anything that
    iterates over it, like a validation report — is deterministic across
    runs.
    """
    found: dict[str, type[Handler[Any, Any]]] = {}

    for module_info in pkgutil.walk_packages(app.application.__path__, prefix="app.application."):
        module = importlib.import_module(module_info.name)
        for _name, obj in inspect.getmembers(module, inspect.isclass):
            if not issubclass(obj, Handler):
                continue
            if obj in _ABSTRACT_HANDLER_TYPES:
                continue
            if inspect.isabstract(obj):
                continue
            # Only count a class in the one module that actually defines it
            # (`obj.__module__ == module.__name__`) — otherwise every module
            # that merely imports a handler class (there are none today, but
            # nothing prevents it) would report it a second time.
            if obj.__module__ != module.__name__:
                continue
            found[f"{obj.__module__}.{obj.__qualname__}"] = obj

    return tuple(found[key] for key in sorted(found))
