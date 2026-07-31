"""Tests for app/application/shared/unit_of_work.py."""

from typing import Any

import pytest

from app.application.shared.repository import Repository
from app.application.shared.unit_of_work import UnitOfWork
from app.domain.shared_kernel.aggregate_root import AggregateRoot
from app.domain.shared_kernel.identifiers import EntityId


class _ThingId(EntityId):
    pass


class _Thing(AggregateRoot[_ThingId]):
    pass


class _ThingRepository(Repository[_Thing, _ThingId]):
    def get(self, entity_id: _ThingId) -> _Thing | None:
        return None

    def add(self, aggregate: _Thing) -> None:
        pass

    def remove(self, aggregate: _Thing) -> None:
        pass


class _FakeUnitOfWork(UnitOfWork):
    """A minimal in-memory implementation, proving the interface is
    actually usable — the same reasoning
    `tests/domain/shared_kernel/test_repository.py`'s own fake
    implementation documents."""

    def __init__(self) -> None:
        self.committed = False
        self.rolled_back = False
        self._thing_repository = _ThingRepository()

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    def get_repository(self, repository_type: type[Any]) -> Any:
        if repository_type is _ThingRepository:
            return self._thing_repository
        raise KeyError(repository_type)


# --- abstractness ---


@pytest.mark.unit
def test_unit_of_work_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        UnitOfWork()  # type: ignore[abstract]


@pytest.mark.unit
def test_a_subclass_missing_an_abstract_method_still_cannot_be_instantiated() -> None:
    class _IncompleteUnitOfWork(UnitOfWork):
        def commit(self) -> None:
            pass

        def rollback(self) -> None:
            pass

        # get_repository() deliberately not implemented

    with pytest.raises(TypeError):
        _IncompleteUnitOfWork()  # type: ignore[abstract]


# --- commit / rollback / get_repository ---


@pytest.mark.unit
def test_commit_and_rollback_and_get_repository() -> None:
    uow = _FakeUnitOfWork()
    assert uow.get_repository(_ThingRepository) is uow._thing_repository

    uow.commit()
    assert uow.committed is True

    uow.rollback()
    assert uow.rolled_back is True


# --- context manager protocol ---


@pytest.mark.unit
def test_enter_returns_self() -> None:
    uow = _FakeUnitOfWork()
    with uow as entered:
        assert entered is uow


@pytest.mark.unit
def test_exit_rolls_back_on_exception_and_does_not_suppress_it() -> None:
    uow = _FakeUnitOfWork()
    with pytest.raises(ValueError, match="boom"), uow:
        raise ValueError("boom")
    assert uow.rolled_back is True
    assert uow.committed is False


@pytest.mark.unit
def test_exit_does_not_auto_commit_on_a_clean_exit() -> None:
    uow = _FakeUnitOfWork()
    with uow:
        pass
    assert uow.committed is False
    assert uow.rolled_back is False


@pytest.mark.unit
def test_a_handler_style_commit_inside_the_block_is_preserved() -> None:
    """Committing is always the caller's own explicit act — proving it
    actually takes effect when a handler does call it inside the
    block."""
    uow = _FakeUnitOfWork()
    with uow:
        uow.commit()
    assert uow.committed is True
    assert uow.rolled_back is False
