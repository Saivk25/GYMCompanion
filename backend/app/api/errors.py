"""Every failure path in this API funnels through this module — either a
route calling one of the `unwrap_or_*` helpers below on an
`ApplicationResult`, or one of the global exception handlers
`register_exception_handlers()` installs. Both ends produce the exact
same response shape, `app.api.schemas.common.ErrorResponse`, so a client
never needs a different parser for a 404 versus a 422 versus a 500.

**Status code policy for `ApplicationResult.fail(...)`** (no structured
error code exists on that type — see `application_result.py`'s own
docstring — so this policy is keyed on *which kind of handler produced
the failure*, not on the free-text message):

- A GET-by-id query handler (`GetGoalHandler`, `GetWorkoutHandler`, ...)
  has exactly one documented failure mode — "no such resource" (confirmed
  by reading every `GetXHandler` in this codebase: each one's only
  `ApplicationResult.fail(...)` call site is a `None` lookup result) — so
  its failure maps to 404. Use `unwrap_or_404`.
- A command handler (create/update/delete/transition) fails for a
  caller-correctable reason — a referenced user doesn't exist, an
  aggregate invariant rejected the request's values — the same shape a
  400 Bad Request describes. Use `unwrap_or_400`.
- A list query handler (`ListGoalsHandler`, ...) only fails on an
  unexpected exception (confirmed identically) — there is no
  "caller-correctable" failure mode for "list everything", so a failure
  here means something broke, not that the caller asked for something
  invalid. Use `unwrap_or_500`.

**`DomainInvariantViolationError` maps to 422**, not 500: in practice
(confirmed by reading `app/domain/*/value_objects.py` in full — see
`docs/adr/0031-fastapi-api-layer.md`, decision 3) this codebase's value
objects raise this same exception type for both "structurally
impossible internal state" *and* "the caller supplied a value outside
the type's own valid range" (`GoalName("")`, `Priority(99)`, ...) — the
second case is exactly what a schema's `to_command()` triggers when
asked to build a value object from bad request data, and that is a
client input error (422 Unprocessable Entity), not a server bug (500).

**`RequestValidationError` (FastAPI/Pydantic's own request-shape
validation, e.g. a missing required field or a `str` where a `date` was
expected) also maps to 422** — re-wrapped into the same `ErrorResponse`
envelope FastAPI's own default handler does not use, so a client sees
one consistent shape regardless of which validation layer rejected the
request.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TypeVar

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.schemas.common import ErrorResponse
from app.application.shared.application_result import ApplicationResult
from app.domain.shared_kernel.errors import DomainInvariantViolationError

logger = logging.getLogger(__name__)

T = TypeVar("T")

_MISSING_VALUE_DETAIL = "handler reported success but returned no value"


def _error_detail(errors: Sequence[str]) -> str | list[str]:
    """A single error collapses to a bare string; more than one becomes
    a list — matching `ErrorResponse.detail`'s own `str | list[str]`
    shape, and avoiding a single-element-list wrapper for the overwhelmingly
    common one-error case.
    """
    if len(errors) == 1:
        return errors[0]
    return list(errors)


def _unwrap_or(result: ApplicationResult[T], *, failure_status: int) -> T:
    if not result.success:
        raise HTTPException(status_code=failure_status, detail=_error_detail(result.errors))
    if result.value is None:
        # Defensive: every GET-by-id/command/list handler in this codebase
        # returns a real value on success (confirmed by reading each one —
        # see the module docstring). A success with no value reaching here
        # would mean a future handler broke that pattern, not a normal
        # outcome this API's callers should ever see as a 4xx.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=_MISSING_VALUE_DETAIL
        )
    return result.value


def unwrap_or_404(result: ApplicationResult[T]) -> T:
    """For GET-by-id query handlers — see the module docstring."""
    return _unwrap_or(result, failure_status=status.HTTP_404_NOT_FOUND)


def unwrap_or_400(result: ApplicationResult[T]) -> T:
    """For command handlers (create/update/delete/transition) — see the
    module docstring."""
    return _unwrap_or(result, failure_status=status.HTTP_400_BAD_REQUEST)


def unwrap_or_500(result: ApplicationResult[T]) -> T:
    """For list query handlers — see the module docstring."""
    return _unwrap_or(result, failure_status=status.HTTP_500_INTERNAL_SERVER_ERROR)


async def _domain_invariant_violation_handler(
    request: Request, exc: DomainInvariantViolationError
) -> JSONResponse:
    del request  # unused — required by FastAPI's exception handler signature
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(detail=str(exc)).model_dump(),
    )


async def _request_validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    del request
    messages = [
        f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}" for error in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(detail=_error_detail(messages)).model_dump(),
    )


async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    del request
    logger.exception("unhandled exception while processing request", exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(detail="internal server error").model_dump(),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Installs every global exception handler this API relies on.
    Called once, from `app.main.create_app()` — see that module.
    """
    # Starlette's own `add_exception_handler` stub types the handler
    # parameter as `Callable[[Request, Exception], ...]` — it cannot express
    # "a handler for exactly this subclass" more precisely, so a handler
    # typed to its own specific exception (for a clean signature at the
    # call site above) trips mypy here. The runtime behavior is correct:
    # Starlette dispatches by exact exception type match against this exact
    # registry key, so `_domain_invariant_violation_handler` only ever
    # actually receives a `DomainInvariantViolationError`.
    app.add_exception_handler(
        DomainInvariantViolationError,
        _domain_invariant_violation_handler,  # type: ignore[arg-type]
    )
    app.add_exception_handler(
        RequestValidationError,
        _request_validation_error_handler,  # type: ignore[arg-type]
    )
    app.add_exception_handler(Exception, _unhandled_exception_handler)
