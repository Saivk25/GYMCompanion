"""Tests for `discover_handler_types()` — the walk that replaces a
hand-maintained handler list (see the module's own docstring for why).
"""

from __future__ import annotations

import pytest

from app.application.shared.command_handler import CommandHandler
from app.application.shared.interfaces import Handler
from app.application.shared.query_handler import QueryHandler
from app.application.workout.handlers.complete_workout_session_handler import (
    CompleteWorkoutSessionHandler,
)
from app.composition.discovery import discover_handler_types

_EXPECTED_HANDLER_COUNT = 49


@pytest.mark.unit
def test_discovers_every_known_handler() -> None:
    """49 — the 44 handlers this codebase had before the Authentication
    & Authorization phase, plus that phase's own 5
    (`app.application.auth.handlers`: Register, Login, Refresh, Logout,
    GetCurrentUser). Not the 43-then-48 a naive single-line-`class X
    (CommandHandler)` grep would find — `CompleteWorkoutSessionHandler`'s
    class statement spans multiple lines, which is exactly the kind of
    formatting variation a hand-maintained or regex-based list is
    fragile to and an `ast`/`inspect`-based walk is not."""
    handler_types = discover_handler_types()
    assert len(handler_types) == _EXPECTED_HANDLER_COUNT
    assert CompleteWorkoutSessionHandler in handler_types


@pytest.mark.unit
def test_no_duplicates() -> None:
    handler_types = discover_handler_types()
    assert len(handler_types) == len(set(handler_types))


@pytest.mark.unit
def test_abstract_base_types_are_excluded() -> None:
    handler_types = discover_handler_types()
    assert Handler not in handler_types
    assert CommandHandler not in handler_types
    assert QueryHandler not in handler_types


@pytest.mark.unit
def test_every_discovered_type_is_a_concrete_handler_subclass() -> None:
    for handler_type in discover_handler_types():
        assert issubclass(handler_type, Handler)


@pytest.mark.unit
def test_result_is_deterministically_ordered_across_calls() -> None:
    assert discover_handler_types() == discover_handler_types()
