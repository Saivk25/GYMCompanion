"""`Command`: marker base class for every write-operation input the
Application Layer accepts.

A `Command` expresses intent to change state — "log this workout,"
"create this goal" — as an immutable, self-contained value a
`CommandHandler` (`command_handler.py`) receives and acts on. It
carries no fields of its own: giving it fields today would mean
guessing at a shape every future command is forced to inherit, the
same reasoning `app.domain.rules.context.RuleContext` documents for
staying an empty marker. This phase builds no concrete command — that
is a future use case's own responsibility.

Unlike `RuleContext` (a plain marker class), `Command` is itself a
frozen dataclass — the same enforcement trick
`app.domain.shared_kernel.value_object.ValueObject` uses: because this
base is declared `@dataclass(frozen=True)`, a subclass that forgets
`frozen=True` fails at class-definition time, not with a confusing
runtime mutation bug later. A `Command` is data handed to a handler
once and never mutated afterward, the same immutability discipline
every value object in this codebase already follows.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class Command:
    """Marker base for every write-operation input. See the module
    docstring for why it declares no fields of its own, and why it is a
    frozen dataclass rather than a plain marker class.
    """
