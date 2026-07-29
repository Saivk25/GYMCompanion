"""Tests for app/domain/shared_kernel/errors.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.domain.shared_kernel.errors import DomainError, DomainInvariantViolationError


@pytest.mark.unit
def test_domain_error_equality_is_by_value() -> None:
    assert DomainError(code="x", message="m") == DomainError(code="x", message="m")
    assert DomainError(code="x", message="m") != DomainError(code="y", message="m")


@pytest.mark.unit
def test_domain_error_is_immutable() -> None:
    error = DomainError(code="x", message="m")
    with pytest.raises(FrozenInstanceError):
        error.message = "changed"  # type: ignore[misc]


@pytest.mark.unit
def test_domain_invariant_violation_is_a_raisable_exception() -> None:
    """DomainError is a value (never raised); DomainInvariantViolationError
    is the opposite — always raised, never returned inside a Result. This
    just proves it behaves like a normal Python exception."""
    with pytest.raises(DomainInvariantViolationError, match="broken"):
        raise DomainInvariantViolationError("broken")


@pytest.mark.unit
def test_domain_invariant_violation_is_not_a_domain_error() -> None:
    """The two failure kinds are deliberately not related by inheritance —
    mixing them up (e.g. accidentally catching one as the other) should
    not be possible by accident."""
    assert not issubclass(DomainInvariantViolationError, DomainError)
    assert not issubclass(DomainError, DomainInvariantViolationError)
