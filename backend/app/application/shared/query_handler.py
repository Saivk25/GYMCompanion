"""`QueryHandler[TQuery, TResult]`: the generic interface every future
concrete read-side handler implements.

The read-side counterpart to `CommandHandler` (`command_handler.py`) —
same shape, same reasoning, narrowing `Handler`'s input type to `Query`
(`query.py`) instead of `Command`. A concrete query handler (e.g.
`class GetActiveGoalHandler(QueryHandler[GetActiveGoalQuery,
GoalContext])`, a future use case this phase does not build) is
expected to load and read domain state — never to mutate it or commit
a `UnitOfWork` for anything beyond what reading requires.
"""

from __future__ import annotations

from typing import TypeVar

from app.application.shared.interfaces import Handler
from app.application.shared.query import Query

TQuery = TypeVar("TQuery", bound=Query)
TResult = TypeVar("TResult")


class QueryHandler(Handler[TQuery, TResult]):
    """Abstract contract for a read-side handler: receives one
    `TQuery`, returns one `ApplicationResult[TResult]`. See
    `Handler.handle()`'s own docstring for what a concrete
    implementation may and may not do.
    """
