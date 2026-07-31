"""Tests for app/application/shared/application_result.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.application.shared.application_result import ApplicationResult
from app.application.shared.exceptions import ApplicationResultConstructionError

# --- construction invariants ---


@pytest.mark.unit
def test_a_successful_result_with_errors_is_rejected() -> None:
    with pytest.raises(ApplicationResultConstructionError):
        ApplicationResult(success=True, errors=("boom",))


@pytest.mark.unit
def test_a_failed_result_with_a_value_is_rejected() -> None:
    with pytest.raises(ApplicationResultConstructionError):
        ApplicationResult(success=False, value=1, errors=("boom",))


@pytest.mark.unit
def test_a_failed_result_with_no_errors_is_rejected() -> None:
    with pytest.raises(ApplicationResultConstructionError):
        ApplicationResult(success=False)


@pytest.mark.unit
def test_a_successful_result_with_no_value_is_allowed() -> None:
    """A command whose only job is a side effect has nothing to
    return."""
    result: ApplicationResult[int] = ApplicationResult(success=True)
    assert result.value is None


# --- ok() / fail() factories ---


@pytest.mark.unit
def test_ok_builds_a_successful_result() -> None:
    result = ApplicationResult.ok(42)
    assert result.success is True
    assert result.value == 42
    assert result.errors == ()
    assert result.warnings == ()


@pytest.mark.unit
def test_ok_defaults_value_to_none() -> None:
    result: ApplicationResult[int] = ApplicationResult.ok()
    assert result.value is None


@pytest.mark.unit
def test_ok_carries_warnings() -> None:
    result = ApplicationResult.ok(1, warnings=["be careful"])
    assert result.warnings == ("be careful",)


@pytest.mark.unit
def test_fail_builds_a_failed_result() -> None:
    result: ApplicationResult[int] = ApplicationResult.fail(["went wrong"])
    assert result.success is False
    assert result.value is None
    assert result.errors == ("went wrong",)


@pytest.mark.unit
def test_fail_carries_warnings_too() -> None:
    result: ApplicationResult[int] = ApplicationResult.fail(["went wrong"], warnings=["also this"])
    assert result.warnings == ("also this",)


@pytest.mark.unit
def test_fail_with_multiple_errors() -> None:
    result: ApplicationResult[int] = ApplicationResult.fail(["first", "second"])
    assert result.errors == ("first", "second")


# --- immutability ---


@pytest.mark.unit
def test_is_immutable() -> None:
    result = ApplicationResult.ok(1)
    with pytest.raises(FrozenInstanceError):
        result.value = 2  # type: ignore[misc]
