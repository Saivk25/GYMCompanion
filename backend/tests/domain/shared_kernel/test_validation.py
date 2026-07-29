"""Tests for app/domain/shared_kernel/validation.py."""

import pytest

from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.shared_kernel.validation import ensure, ensure_not_empty, ensure_positive


@pytest.mark.unit
def test_ensure_passes_silently_when_condition_is_true() -> None:
    ensure(True, "unreachable")  # must not raise


@pytest.mark.unit
def test_ensure_raises_with_the_given_message_when_false() -> None:
    with pytest.raises(DomainInvariantViolationError, match="boom"):
        ensure(False, "boom")


@pytest.mark.unit
def test_ensure_not_empty_returns_the_value_when_valid() -> None:
    assert ensure_not_empty("Alice", "name") == "Alice"


@pytest.mark.parametrize("blank", ["", "   ", "\t\n"])
@pytest.mark.unit
def test_ensure_not_empty_rejects_blank_strings(blank: str) -> None:
    with pytest.raises(DomainInvariantViolationError, match="name must not be empty"):
        ensure_not_empty(blank, "name")


@pytest.mark.unit
def test_ensure_positive_returns_the_value_when_valid() -> None:
    assert ensure_positive(1.5, "weight") == 1.5


@pytest.mark.parametrize("bad_value", [0, -1, -0.5])
@pytest.mark.unit
def test_ensure_positive_rejects_zero_and_negative(bad_value: float) -> None:
    with pytest.raises(DomainInvariantViolationError, match="weight must be positive"):
        ensure_positive(bad_value, "weight")
