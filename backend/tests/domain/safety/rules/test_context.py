"""Tests for app/domain/safety/rules/context.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.domain.rules.context import RuleContext
from app.domain.safety.rules.context import ActiveInjury, DeclaredRestriction, SafetyRuleContext
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from tests.domain.safety.rules.factories import (
    a_declared_restriction,
    a_readiness_context,
    a_safety_context,
    an_active_injury,
)

# --- DeclaredRestriction ---


@pytest.mark.unit
def test_declared_restriction_requires_a_non_empty_tag() -> None:
    with pytest.raises(DomainInvariantViolationError, match="tag"):
        DeclaredRestriction(tag="")


@pytest.mark.unit
def test_declared_restriction_defaults_description_to_empty() -> None:
    restriction = DeclaredRestriction(tag="overhead_pressing")
    assert restriction.description == ""


@pytest.mark.unit
def test_declared_restriction_is_immutable() -> None:
    restriction = a_declared_restriction()
    with pytest.raises(FrozenInstanceError):
        restriction.tag = "other"  # type: ignore[misc]


# --- ActiveInjury ---


@pytest.mark.unit
def test_active_injury_requires_a_non_empty_description() -> None:
    with pytest.raises(DomainInvariantViolationError, match="description"):
        ActiveInjury(description="")


@pytest.mark.unit
def test_active_injury_defaults_restricts_training_to_true() -> None:
    injury = ActiveInjury(description="Left shoulder strain")
    assert injury.restricts_training is True


@pytest.mark.unit
def test_active_injury_is_immutable() -> None:
    injury = an_active_injury()
    with pytest.raises(FrozenInstanceError):
        injury.restricts_training = False  # type: ignore[misc]


# --- SafetyRuleContext ---


@pytest.mark.unit
def test_is_a_rule_context() -> None:
    assert isinstance(SafetyRuleContext(), RuleContext)


@pytest.mark.unit
def test_defaults_every_field() -> None:
    context = SafetyRuleContext()
    assert context.readiness is None
    assert context.recent_training is None
    assert context.declared_restrictions == ()
    assert context.active_injuries == ()


@pytest.mark.unit
def test_accepts_every_field_explicitly() -> None:
    readiness = a_readiness_context()
    restriction = a_declared_restriction()
    injury = an_active_injury()
    context = a_safety_context(
        readiness=readiness,
        declared_restrictions=(restriction,),
        active_injuries=(injury,),
    )
    assert context.readiness == readiness
    assert context.declared_restrictions == (restriction,)
    assert context.active_injuries == (injury,)


@pytest.mark.unit
def test_is_immutable() -> None:
    context = SafetyRuleContext()
    with pytest.raises(FrozenInstanceError):
        context.readiness = a_readiness_context()  # type: ignore[misc]


@pytest.mark.unit
def test_two_empty_contexts_do_not_share_a_mutable_tuple_instance() -> None:
    """Guards against a classic mutable-default-argument-style bug: each
    `SafetyRuleContext()` call must get its own empty tuple, not the same
    shared default object silently reused."""
    first = SafetyRuleContext()
    second = SafetyRuleContext()
    assert first.declared_restrictions == second.declared_restrictions
    assert first.declared_restrictions is not None
