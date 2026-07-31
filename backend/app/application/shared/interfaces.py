"""`Handler[TInput, TResult]`: the one generic structural interface
`CommandHandler` and `QueryHandler` both specialize.

Both handler kinds collapse to the exact same shape — receive one
input, return one `ApplicationResult` — the same way CQRS itself treats
the command/query split as a naming and intent distinction, not a
structural one. Defining that one shape here, once, and having
`command_handler.py`/`query_handler.py` each narrow it to their own
input type (`Command`/`Query` respectively) keeps the two from
silently drifting apart if a future change touches only one of them,
and gives this module a distinct, non-overlapping purpose from every
other file in this package: everything else here names one concrete
concept (a command, a query, a result, a unit of work, ...); this one
names the shared shape underneath two of them.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from app.application.shared.application_result import ApplicationResult

TInput = TypeVar("TInput")
TResult = TypeVar("TResult")


class Handler(ABC, Generic[TInput, TResult]):
    """Abstract contract: receives one `TInput`, returns one
    `ApplicationResult[TResult]`. Every method is abstract — this class
    cannot be instantiated on its own, only subclassed (directly, or
    through `CommandHandler`/`QueryHandler`) by a real handler.
    """

    @abstractmethod
    def handle(self, request: TInput) -> ApplicationResult[TResult]:
        """Executes this handler's workflow for `request` and returns
        exactly one `ApplicationResult`. A concrete implementation
        orchestrates domain code — loading aggregates through a
        `Repository`, invoking a rule engine, committing a
        `UnitOfWork`, dispatching domain events through a
        `DomainEventDispatcher` — but contains no business rule of its
        own; every such decision belongs to `app.domain`.
        """
        raise NotImplementedError  # pragma: no cover — abstract, always overridden
