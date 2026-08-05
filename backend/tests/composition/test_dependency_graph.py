"""The dependency-graph-validation test: "every handler can resolve its
dependencies," "every repository can be constructed," and "UnitOfWork
returns the correct repository," proven for the *entire* real dependency
graph this codebase has — not a sampled few handlers — the same
guarantee `Container.validate()` gives at process startup
(`app/composition/bootstrap.py`), exercised here independently as a
dedicated, always-run test rather than only as a side effect of
`test_bootstrap.py` constructing one `Container`.
"""

from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy import create_engine

from app.application.shared.interfaces import Handler
from app.composition.container import Container, build_container
from app.composition.discovery import discover_handler_types
from app.core.config import Settings
from app.domain.shared_kernel.repository import Repository
from app.domain.user.repository import UserRepository
from app.infra.unit_of_work import DEFAULT_REPOSITORY_FACTORIES, SqlAlchemyUnitOfWork


@pytest.fixture
def container() -> Container:
    engine = create_engine("sqlite://")
    return build_container(Settings(), engine)


@pytest.mark.unit
def test_validate_passes_for_the_real_container(container: Container) -> None:
    container.validate()


@pytest.mark.unit
@pytest.mark.parametrize("handler_type", discover_handler_types())
def test_every_discovered_handler_resolves_to_an_instance_of_itself(
    container: Container, handler_type: type[Handler[Any, Any]]
) -> None:
    instance = container.handler(handler_type)
    assert isinstance(instance, handler_type)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("repository_type", "expected_concrete_type"),
    list(DEFAULT_REPOSITORY_FACTORIES.items()),
)
def test_every_registered_repository_constructs_against_a_real_session(
    container: Container,
    repository_type: type[Repository[Any, Any]],
    expected_concrete_type: type[Repository[Any, Any]],
) -> None:
    """Constructing a repository does no I/O (see `SqlAlchemyUnitOfWork`'s
    own docstring), so this runs against `container`'s real
    `session_factory` with no live database required — proving the
    registry entry actually produces the type it claims to, for all
    eight aggregates at once."""
    with container.unit_of_work() as uow:
        repository = uow.get_repository(repository_type)
    assert isinstance(repository, expected_concrete_type)
    assert isinstance(repository, repository_type)


@pytest.mark.unit
def test_unit_of_work_caches_repositories_within_one_with_block_but_not_across(
    container: Container,
) -> None:
    uow = container.unit_of_work()
    assert isinstance(uow, SqlAlchemyUnitOfWork)

    with uow as opened:
        first = opened.get_repository(UserRepository)  # type: ignore[type-abstract]
        second = opened.get_repository(UserRepository)  # type: ignore[type-abstract]
    assert first is second

    with uow as reopened:
        third = reopened.get_repository(UserRepository)  # type: ignore[type-abstract]
    assert third is not first
