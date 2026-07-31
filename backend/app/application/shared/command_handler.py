"""`CommandHandler[TCommand, TResult]`: the generic interface every
future concrete write-side handler implements.

A thin, purpose-named specialization of `Handler`
(`interfaces.py`) — narrows the input type to `Command`
(`command.py`) so a handler's own class signature (e.g.
`class LogWorkoutHandler(CommandHandler[LogWorkoutCommand, WorkoutId])`,
a future use case this phase does not build) self-documents that it
performs a write, without repeating `Handler`'s own `handle()`
contract.
"""

from __future__ import annotations

from typing import TypeVar

from app.application.shared.command import Command
from app.application.shared.interfaces import Handler

TCommand = TypeVar("TCommand", bound=Command)
TResult = TypeVar("TResult")


class CommandHandler(Handler[TCommand, TResult]):
    """Abstract contract for a write-side handler: receives one
    `TCommand`, returns one `ApplicationResult[TResult]`. See
    `Handler.handle()`'s own docstring for what a concrete
    implementation may and may not do.
    """
