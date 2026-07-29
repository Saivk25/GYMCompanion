"""Tests for app/domain/rules/context.py.

`RuleContext` itself declares no fields and no behavior — see its module
docstring for why. These tests only prove it's usable as a base class the
way a future concrete engine's own context is expected to use it.
"""

import pytest

from app.domain.rules.context import RuleContext
from tests.domain.rules.factories import DummyContext


@pytest.mark.unit
def test_rule_context_can_be_instantiated_directly() -> None:
    """Not abstract — a marker base, not an ABC with abstract methods."""
    assert isinstance(RuleContext(), RuleContext)


@pytest.mark.unit
def test_a_concrete_subclass_is_a_rule_context() -> None:
    context = DummyContext(value=5)
    assert isinstance(context, RuleContext)
    assert context.value == 5
