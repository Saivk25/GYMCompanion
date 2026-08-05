"""Tests for `Container` — handler resolution, the sharing/no-sharing
split between collaborators, and `validate()`'s ability to actually
detect a broken dependency graph, not just report success on the one
that already works.

Builds `Container` directly via `build_container()`, not
`bootstrap()` (that combination is `tests/composition/test_bootstrap.
py`'s job) — these tests are about `Container`'s own resolution logic in
isolation.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine

from app.application.goal.handlers.get_goal_handler import GetGoalHandler
from app.application.shared.exceptions import UnitOfWorkError
from app.application.user.handlers.create_user_handler import CreateUserHandler
from app.application.user.handlers.deactivate_user_handler import DeactivateUserHandler
from app.application.user.handlers.get_user_handler import GetUserHandler
from app.composition.container import CompositionError, Container, build_container
from app.core.config import Settings
from app.domain.exercise.repository import ExerciseRepository
from app.domain.shared_kernel.clock import SystemClock
from app.domain.user.repository import UserRepository
from app.infra.repositories.exercise_repository import ExerciseSqlRepository
from app.infra.repositories.user_repository import UserSqlRepository
from app.infra.unit_of_work import DEFAULT_REPOSITORY_FACTORIES, SqlAlchemyUnitOfWork


@pytest.fixture
def container() -> Container:
    # sqlite, not the real Postgres URL: constructing a Container/Engine
    # does no I/O (see app/infra/unit_of_work.py's own docstring), so any
    # syntactically valid SQLAlchemy URL works here — sqlite keeps these
    # tests independent of GYM_DATABASE_URL/a reachable Postgres.
    engine = create_engine("sqlite://")
    return build_container(Settings(), engine)


@pytest.mark.unit
def test_unit_of_work_is_a_fresh_instance_every_call(container: Container) -> None:
    first = container.unit_of_work()
    second = container.unit_of_work()
    assert isinstance(first, SqlAlchemyUnitOfWork)
    assert first is not second


@pytest.mark.unit
def test_handler_with_uow_only_shape_resolves(container: Container) -> None:
    handler = container.handler(GetUserHandler)
    assert isinstance(handler, GetUserHandler)
    assert isinstance(handler._uow, SqlAlchemyUnitOfWork)


@pytest.mark.unit
def test_handler_with_uow_and_dispatcher_shape_resolves(container: Container) -> None:
    handler = container.handler(DeactivateUserHandler)
    assert isinstance(handler, DeactivateUserHandler)
    assert handler._dispatcher is container.dispatcher


@pytest.mark.unit
def test_handler_with_uow_dispatcher_and_clock_shape_resolves(container: Container) -> None:
    handler = container.handler(CreateUserHandler)
    assert isinstance(handler, CreateUserHandler)
    assert handler._dispatcher is container.dispatcher
    assert handler._clock is container.clock


@pytest.mark.unit
def test_two_resolutions_of_the_same_handler_type_get_independent_uows(
    container: Container,
) -> None:
    """The concurrency-safety property `app/infra/unit_of_work.py` and
    `container.py`'s own module docstrings both argue for at length:
    resolving the same handler type twice must never hand back the same
    `UnitOfWork` (or the same handler instance)."""
    first = container.handler(GetGoalHandler)
    second = container.handler(GetGoalHandler)
    assert first is not second
    assert first._uow is not second._uow


@pytest.mark.unit
def test_clock_and_dispatcher_are_shared_singletons_across_resolutions(
    container: Container,
) -> None:
    first = container.handler(CreateUserHandler)
    second = container.handler(CreateUserHandler)
    assert first._clock is second._clock is container.clock
    assert first._dispatcher is second._dispatcher is container.dispatcher
    assert isinstance(container.clock, SystemClock)


@pytest.mark.unit
def test_unit_of_work_returns_the_correct_repository_type(container: Container) -> None:
    with container.unit_of_work() as uow:
        user_repository = uow.get_repository(UserRepository)  # type: ignore[type-abstract]
        exercise_repository = uow.get_repository(ExerciseRepository)  # type: ignore[type-abstract]
    assert isinstance(user_repository, UserSqlRepository)
    assert isinstance(exercise_repository, ExerciseSqlRepository)


@pytest.mark.unit
def test_unit_of_work_get_repository_for_unregistered_type_raises(container: Container) -> None:
    with container.unit_of_work() as uow, pytest.raises(UnitOfWorkError):
        # Repository (the bare shared-kernel base, never registered under
        # itself — every real registration is keyed by a concrete
        # aggregate's own abstract subtype) is deliberately not in
        # DEFAULT_REPOSITORY_FACTORIES.
        from app.domain.shared_kernel.repository import Repository

        uow.get_repository(Repository)  # type: ignore[type-abstract]


@pytest.mark.unit
def test_validate_succeeds_for_a_correctly_wired_container(container: Container) -> None:
    container.validate()  # must not raise


@pytest.mark.unit
def test_validate_detects_a_repository_factory_registered_under_the_wrong_type(
    container: Container, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Proves `validate()` actually checks something, rather than always
    passing — deliberately mis-registers `ExerciseSqlRepository` under
    `UserRepository`'s key and confirms `validate()` catches the
    mismatch. Patches the name as it is bound inside `app.composition.
    container` (not `app.infra.unit_of_work`, where it originates) —
    `_validate_repository_registrations` resolves `DEFAULT_REPOSITORY_
    FACTORIES` as a global in its own module's namespace at call time, so
    that is the binding that must change for this test to actually
    exercise the failure path."""
    import app.composition.container as container_module

    tampered = dict(DEFAULT_REPOSITORY_FACTORIES)
    tampered[UserRepository] = ExerciseSqlRepository  # type: ignore[type-abstract]
    monkeypatch.setattr(container_module, "DEFAULT_REPOSITORY_FACTORIES", tampered)

    with pytest.raises(CompositionError, match="is not an instance of it"):
        container.validate()
