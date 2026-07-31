"""Tests for app/application/shared/repository.py."""

import pytest

from app.application.shared.repository import Repository
from app.domain.shared_kernel.repository import Repository as DomainRepository


@pytest.mark.unit
def test_is_the_same_type_as_the_domain_repository() -> None:
    """The whole point of this module: no second, parallel interface —
    just a re-export under the Application Layer's own import path."""
    assert Repository is DomainRepository


@pytest.mark.unit
def test_repository_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        Repository()  # type: ignore[abstract]
