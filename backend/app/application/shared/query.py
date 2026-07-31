"""`Query`: marker base class for every read-operation input the
Application Layer accepts.

The read-side counterpart to `Command` (`command.py`) — same shape,
same reasoning, distinguished only by name so a handler's own type
signature self-documents whether it reads or writes. A `Query`
expresses a request for information — "get this user's active goal,"
"list this week's completed sessions" — never a state change.

See `command.py`'s own docstring for the full reasoning behind the
frozen-dataclass-as-marker-base choice; it applies identically here.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class Query:
    """Marker base for every read-operation input. See the module
    docstring, and `command.py`'s, for why it declares no fields of its
    own and why it is a frozen dataclass rather than a plain marker
    class.
    """
