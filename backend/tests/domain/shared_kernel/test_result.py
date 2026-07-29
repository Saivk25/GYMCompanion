"""Tests for app/domain/shared_kernel/result.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.domain.shared_kernel.errors import DomainError
from app.domain.shared_kernel.result import Err, Ok, unwrap_or


@pytest.mark.unit
def test_ok_carries_its_value_and_reports_is_ok() -> None:
    result = Ok(42)
    assert result.is_ok is True
    assert result.is_err is False
    assert result.value == 42


@pytest.mark.unit
def test_err_carries_its_error_and_reports_is_err() -> None:
    error = DomainError(code="oops", message="something went wrong")
    result = Err(error)
    assert result.is_ok is False
    assert result.is_err is True
    assert result.error == error


@pytest.mark.unit
def test_ok_has_no_error_attribute() -> None:
    """Ok and Err are separate types specifically so accessing the wrong
    side is a static (mypy) and immediate (AttributeError) failure, never
    a silent None."""
    result = Ok(42)
    assert not hasattr(result, "error")


@pytest.mark.unit
def test_err_has_no_value_attribute() -> None:
    result = Err(DomainError(code="oops", message="bad"))
    assert not hasattr(result, "value")


@pytest.mark.unit
def test_isinstance_narrows_ok_vs_err() -> None:
    results: list[Ok[int] | Err[DomainError]] = [
        Ok(1),
        Err(DomainError(code="x", message="x")),
    ]
    oks = [r.value for r in results if isinstance(r, Ok)]
    errs = [r.error for r in results if isinstance(r, Err)]
    assert oks == [1]
    assert len(errs) == 1


@pytest.mark.unit
def test_unwrap_or_returns_the_value_on_ok() -> None:
    assert unwrap_or(Ok(42), default=0) == 42


@pytest.mark.unit
def test_unwrap_or_returns_the_default_on_err() -> None:
    result: Err[DomainError] = Err(DomainError(code="x", message="x"))
    assert unwrap_or(result, default=0) == 0


@pytest.mark.unit
def test_ok_is_immutable() -> None:
    result = Ok(42)
    with pytest.raises(FrozenInstanceError):
        result.value = 43  # type: ignore[misc]


@pytest.mark.unit
def test_err_is_immutable() -> None:
    result = Err(DomainError(code="x", message="x"))
    with pytest.raises(FrozenInstanceError):
        result.error = DomainError(code="y", message="y")  # type: ignore[misc]


@pytest.mark.unit
def test_ok_equality_is_by_value() -> None:
    assert Ok(42) == Ok(42)
    assert Ok(42) != Ok(43)
