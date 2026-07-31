"""Tests for app/application/shared/exceptions.py."""

import pytest

from app.application.shared.exceptions import (
    ApplicationError,
    ApplicationResultConstructionError,
    DomainEventDispatchError,
    UnitOfWorkError,
)
from app.domain.shared_kernel.errors import DomainInvariantViolationError


@pytest.mark.unit
@pytest.mark.parametrize(
    "exception_type",
    [ApplicationResultConstructionError, UnitOfWorkError, DomainEventDispatchError],
)
def test_every_application_exception_is_an_application_error(
    exception_type: type[ApplicationError],
) -> None:
    assert issubclass(exception_type, ApplicationError)


@pytest.mark.unit
def test_application_error_is_a_plain_exception() -> None:
    assert issubclass(ApplicationError, Exception)


@pytest.mark.unit
def test_application_errors_are_raisable_and_catchable() -> None:
    with pytest.raises(ApplicationError):
        raise ApplicationResultConstructionError("bad shape")


@pytest.mark.unit
def test_application_error_does_not_duplicate_domain_error_types() -> None:
    """The whole point of this module: a distinct hierarchy, not a
    second copy of the Domain Layer's own exception types."""
    assert not issubclass(ApplicationError, DomainInvariantViolationError)
    assert not issubclass(DomainInvariantViolationError, ApplicationError)
