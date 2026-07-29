"""Tests for app/domain/workout_session/value_objects.py."""

from dataclasses import FrozenInstanceError
from datetime import date, timedelta

import pytest

from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.workout_session.value_objects import (
    CompletionPercentage,
    SessionDate,
    SessionDuration,
    SessionNotes,
    SessionRating,
)

# --- SessionDate ---


@pytest.mark.unit
def test_session_date_wraps_a_date() -> None:
    assert SessionDate(date(2026, 1, 1)).value == date(2026, 1, 1)


@pytest.mark.unit
def test_session_date_is_immutable() -> None:
    session_date = SessionDate(date(2026, 1, 1))
    with pytest.raises(FrozenInstanceError):
        session_date.value = date(2026, 1, 2)  # type: ignore[misc]


@pytest.mark.unit
def test_session_date_equality_is_by_value() -> None:
    assert SessionDate(date(2026, 1, 1)) == SessionDate(date(2026, 1, 1))
    assert SessionDate(date(2026, 1, 1)) != SessionDate(date(2026, 1, 2))


# --- SessionDuration ---


@pytest.mark.unit
def test_session_duration_accepts_a_positive_timedelta() -> None:
    duration = SessionDuration(timedelta(minutes=45))
    assert duration.value == timedelta(minutes=45)


@pytest.mark.unit
def test_session_duration_rejects_exactly_zero() -> None:
    """Deliberately stricter than WorkoutDuration, which allows zero —
    see the class docstring for why."""
    with pytest.raises(DomainInvariantViolationError, match="must be positive"):
        SessionDuration(timedelta(0))


@pytest.mark.unit
def test_session_duration_rejects_a_negative_timedelta() -> None:
    with pytest.raises(DomainInvariantViolationError, match="must be positive"):
        SessionDuration(timedelta(minutes=-1))


@pytest.mark.unit
def test_session_duration_is_immutable() -> None:
    duration = SessionDuration(timedelta(minutes=45))
    with pytest.raises(FrozenInstanceError):
        duration.value = timedelta(minutes=50)  # type: ignore[misc]


# --- SessionNotes ---


@pytest.mark.unit
def test_session_notes_defaults_to_empty() -> None:
    assert SessionNotes().value == ""


@pytest.mark.unit
def test_session_notes_accepts_an_explicitly_empty_value() -> None:
    """ "Notes may be empty" — an explicit empty string is not an error
    here, unlike WorkoutNotes/ExerciseDescription."""
    assert SessionNotes("").value == ""


@pytest.mark.unit
def test_session_notes_accepts_a_non_empty_value() -> None:
    assert SessionNotes("Felt strong today.").value == "Felt strong today."


@pytest.mark.unit
def test_session_notes_rejects_an_overly_long_value() -> None:
    with pytest.raises(DomainInvariantViolationError, match="at most 2000 characters"):
        SessionNotes("x" * 2001)


@pytest.mark.unit
def test_session_notes_is_immutable() -> None:
    notes = SessionNotes("Felt strong today.")
    with pytest.raises(FrozenInstanceError):
        notes.value = "Changed"  # type: ignore[misc]


# --- SessionRating ---


@pytest.mark.unit
@pytest.mark.parametrize("value", [1, 5, 10])
def test_session_rating_accepts_values_within_bounds(value: int) -> None:
    assert SessionRating(value).value == value


@pytest.mark.unit
@pytest.mark.parametrize("value", [0, -1, 11])
def test_session_rating_rejects_values_outside_bounds(value: int) -> None:
    with pytest.raises(DomainInvariantViolationError, match="must be between 1 and 10"):
        SessionRating(value)


@pytest.mark.unit
def test_session_rating_is_immutable() -> None:
    rating = SessionRating(5)
    with pytest.raises(FrozenInstanceError):
        rating.value = 6  # type: ignore[misc]


# --- CompletionPercentage ---


@pytest.mark.unit
@pytest.mark.parametrize("value", [0.0, 50.0, 100.0])
def test_completion_percentage_accepts_values_within_bounds(value: float) -> None:
    assert CompletionPercentage(value).value == value


@pytest.mark.unit
@pytest.mark.parametrize("value", [-0.1, 100.1])
def test_completion_percentage_rejects_values_outside_bounds(value: float) -> None:
    with pytest.raises(DomainInvariantViolationError, match=r"must be between 0.0 and 100.0"):
        CompletionPercentage(value)


@pytest.mark.unit
def test_completion_percentage_is_immutable() -> None:
    completion = CompletionPercentage(100.0)
    with pytest.raises(FrozenInstanceError):
        completion.value = 50.0  # type: ignore[misc]
