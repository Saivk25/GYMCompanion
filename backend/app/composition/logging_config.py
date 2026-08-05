"""Logging configuration: the one call site in this codebase that touches
the stdlib `logging` module's global state (`logging.basicConfig`).

Every other module that wants to log gets its own `logging.getLogger(
__name__)` (the standard, hierarchical-namespace pattern) and relies on
this function having already configured the *root* logger's handler and
level once, at process startup — the same "configure once, at the
composition root; consume everywhere via injection or, for logging
specifically, the stdlib's own module-name-hierarchy lookup" discipline
`app/domain/shared_kernel/clock.py` documents for `Clock`. No module
under `app.domain`, `app.application`, or `app.infra` calls
`logging.basicConfig`/`logging.getLogger().setLevel(...)` itself — doing
so anywhere but here would make log verbosity a scattered, hard-to-audit
property of whichever module happened to run first.

Deliberately not structured/JSON logging, a `logging.config.dictConfig`,
or a third-party logging library (`structlog`, `loguru`): this phase's
own task is "make the application executable... without HTTP endpoints",
not "build production observability tooling" — a text formatter with the
level, logger name, and message is enough to prove logging is wired at
all (see `test_bootstrap.py`'s `caplog`-based assertion that a log record
is actually emitted), and reaches for `dictConfig`'s handler/formatter
graph only when a real requirement (e.g. shipping structured logs to an
aggregator) asks for it — not speculatively, the same reasoning ADR 0029
already gives for rejecting SQLAlchemy's classical mapping ahead of an
actual need.
"""

from __future__ import annotations

import logging

from app.core.config import Settings

_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def configure_logging(settings: Settings) -> None:
    """Configures the root logger's level (from `settings.log_level`) and
    a single stream handler with a fixed, readable format. Idempotent:
    safe to call more than once (e.g. once from `bootstrap()` and once
    from a test that also wants logging configured) — `force=True` tells
    `logging.basicConfig` to replace any handlers a prior call already
    installed, rather than silently no-op the way `basicConfig` does by
    default once any handler exists.
    """
    logging.basicConfig(level=settings.log_level, format=_FORMAT, force=True)
