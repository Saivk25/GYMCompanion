"""The Application Layer Foundation: framework-independent interfaces
every future use case (a later phase's own responsibility) builds on.

This package defines shapes, not behavior: `Command`/`Query` (write and
read inputs), `Handler`/`CommandHandler`/`QueryHandler` (the contract a
future use case implements), `ApplicationResult` (what every handler
returns), `Repository` (re-exported from the Domain Layer, not
redefined), `UnitOfWork` (the transactional boundary a handler runs
inside), `DomainEventDispatcher` (how a handler publishes what an
aggregate recorded), this layer's own exception hierarchy,
`advisory_warnings()` (formats a Domain Layer `RuleResult`'s
recommendations for a handler to surface as
`ApplicationResult.warnings` — see that function's own module
docstring for why it lives here rather than in `app.domain.rules`), and
`ensure_owner()` (the single "does the caller own this resource"
comparison every ownership-checked handler calls — see that function's
own module docstring for why it lives here rather than the API or
Domain Layer). No concrete command, query, handler, repository
implementation, or dispatcher exists yet — see `docs/adr/0022-
application-layer-foundation.md` for the full architecture, including
why orchestration belongs in this layer rather than the Domain Layer or
a future infrastructure layer, and why several of these interfaces
reuse rather than duplicate a Domain Layer type that already covers the
same concept.

Re-exported here so a future use-case module can write one import
instead of many:

    from app.application.shared import Command, CommandHandler, ApplicationResult

rather than reaching into each submodule individually — the same
convention `app.domain.shared_kernel.__init__`'s own docstring
documents for the Domain Core.

Depends on nothing outside the Python standard library and
`app.domain` — enforced by
`tests/application/test_import_boundaries.py`, mirroring
`tests/domain/test_import_boundaries.py`'s rule for `app/domain`.
"""

from app.application.shared.advisory_warnings import advisory_warnings
from app.application.shared.application_result import ApplicationResult
from app.application.shared.command import Command
from app.application.shared.command_handler import CommandHandler
from app.application.shared.domain_event_dispatcher import DomainEventDispatcher
from app.application.shared.exceptions import (
    ApplicationError,
    ApplicationResultConstructionError,
    DomainEventDispatchError,
    UnitOfWorkError,
)
from app.application.shared.interfaces import Handler
from app.application.shared.ownership import ensure_owner
from app.application.shared.query import Query
from app.application.shared.query_handler import QueryHandler
from app.application.shared.repository import Repository
from app.application.shared.unit_of_work import UnitOfWork

__all__ = [
    "ApplicationError",
    "ApplicationResult",
    "ApplicationResultConstructionError",
    "Command",
    "CommandHandler",
    "DomainEventDispatchError",
    "DomainEventDispatcher",
    "Handler",
    "Query",
    "QueryHandler",
    "Repository",
    "UnitOfWork",
    "UnitOfWorkError",
    "advisory_warnings",
    "ensure_owner",
]
