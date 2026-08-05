"""Shared schema types and the value-object <-> primitive conversion
helper every module's schema file uses.

**Convention**: every domain value object in this codebase wraps exactly
one primitive in a `.value` attribute (`str`, `float`, `int`, or `date`
— confirmed across all five modules this phase exposes: `GoalName.value:
str`, `TargetWeight.value: float`, `Priority.value: int`, `TargetDate.
value: date`, and so on, with no exception). `unwrap()`/`unwrap_optional()`
below are the one place that pattern is spelled out, so every schema's
own `from_dto()` reads `unwrap_optional(dto.notes)` rather than
`dto.notes.value if dto.notes is not None else None` repeated at every
call site.

**Why Pydantic schemas exist at all, given the Application Layer already
has DTOs (`WorkoutDTO`, `GoalDTO`, ...).** Returning a DTO directly from
a FastAPI route would put every domain value object (`WorkoutName`,
`TargetDate`, ...) directly into the JSON response, which FastAPI cannot
serialize without a value-object-aware `json_encoders` configuration
duplicated across every response model — and, more importantly, would
make the API's public JSON shape a direct function of internal domain
types that are free to change for domain reasons (see `docs/adr/0031-
fastapi-api-layer.md`, decision 2). A dedicated schema per DTO, each
`from_dto()` performing the (mechanical, one-line-per-field) unwrap, is
what keeps "the API is thin" true without also making the API's JSON
shape brittle to a value object being renamed or restructured for a
reason that has nothing to do with the HTTP contract.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Protocol, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")
# Covariant, not invariant: every value object's `.value` is immutable
# (frozen dataclass), so it is read-only from this Protocol's point of
# view -- declaring it as a `@property` rather than a plain attribute is
# what lets mypy structurally match e.g. `GoalName` (`value: str`)
# against `_HasValue[T_co]` and infer `T_co = str` at each call site. An
# invariant plain-attribute Protocol (`value: T`) cannot be inferred this
# way from a bare structural argument -- mypy has no other constraint to
# pin `T` down and falls back to `Never`, rejecting every real call site.
T_co = TypeVar("T_co", covariant=True)


class _HasValue(Protocol[T_co]):
    """Structural type for "any of this codebase's value objects" — every
    one has exactly a `.value: T` attribute, see the module docstring."""

    @property
    def value(self) -> T_co: ...


def unwrap(value_object: _HasValue[T_co]) -> T_co:
    """Unwraps a required value object to its primitive."""
    return value_object.value


def unwrap_optional(value_object: _HasValue[T_co] | None) -> T_co | None:
    """Unwraps an optional value object to its primitive, passing
    `None` through unchanged."""
    return None if value_object is None else value_object.value


def duration_to_seconds(duration: timedelta) -> float:
    """`WorkoutDuration`/`SessionDuration`/`SleepDuration` all wrap a
    `datetime.timedelta` — represented over HTTP as a plain number of
    seconds, the simplest JSON-safe shape a `timedelta` has, rather than
    an ISO-8601 duration string this API has no other reason to parse.
    """
    return duration.total_seconds()


def seconds_to_duration(seconds: float) -> timedelta:
    return timedelta(seconds=seconds)


class IdResponse(BaseModel):
    """The response body for every mutation endpoint (create/update/
    transition) in this API: the affected aggregate's id, and any
    advisory `warnings` the invoked rule engine produced (see
    `ApplicationResult.warnings` — never a reason a command fails, only
    something worth telling the caller). Deliberately not the full
    updated resource — see ADR 0031 decision 5 for why every mutation
    endpoint returns this instead of re-fetching and returning the whole
    aggregate.
    """

    id: str = Field(description="The affected aggregate's id.")
    warnings: tuple[str, ...] = Field(
        default=(), description="Advisory messages from an invoked rule engine, if any."
    )


class ErrorResponse(BaseModel):
    """The one error response shape every failure path in this API
    returns — `RequestValidationError`, `DomainInvariantViolationError`,
    an `ApplicationResult.fail(...)`, and an unhandled exception all
    produce this same envelope (see `app/api/errors.py`), so a client
    never needs a different parser for a 404 versus a 422 versus a 500.
    """

    detail: str | list[str] = Field(description="A human-readable error message, or several.")
