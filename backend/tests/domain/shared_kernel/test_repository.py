"""Tests for app/domain/shared_kernel/repository.py."""

import pytest

from app.domain.shared_kernel.aggregate_root import AggregateRoot
from app.domain.shared_kernel.identifiers import EntityId
from app.domain.shared_kernel.repository import Repository


class _UserId(EntityId):
    pass


class _User(AggregateRoot[_UserId]):
    pass


@pytest.mark.unit
def test_repository_cannot_be_instantiated_directly() -> None:
    """The whole point of the interface: `app/domain` can depend on
    `Repository[...]` without ever being able to accidentally construct a
    usable-but-fake one that skips a real implementation's guarantees."""
    with pytest.raises(TypeError):
        Repository()  # type: ignore[abstract]


@pytest.mark.unit
def test_subclass_missing_an_abstract_method_still_cannot_be_instantiated() -> None:
    class _IncompleteRepository(Repository[_User, _UserId]):
        def get(self, entity_id: _UserId) -> _User | None:
            return None

        def add(self, aggregate: _User) -> None:
            pass

        # remove() deliberately not implemented

    with pytest.raises(TypeError):
        _IncompleteRepository()  # type: ignore[abstract]


@pytest.mark.unit
def test_a_complete_subclass_can_be_instantiated_and_used() -> None:
    """A minimal, in-memory implementation — proving the interface is
    actually usable, not just abstract. Real implementations (Postgres-
    backed) arrive in app/infra/ starting Sprint 2."""

    class _InMemoryUserRepository(Repository[_User, _UserId]):
        def __init__(self) -> None:
            self._users: dict[_UserId, _User] = {}

        def get(self, entity_id: _UserId) -> _User | None:
            return self._users.get(entity_id)

        def add(self, aggregate: _User) -> None:
            self._users[aggregate.id] = aggregate

        def remove(self, aggregate: _User) -> None:
            del self._users[aggregate.id]

    repo = _InMemoryUserRepository()
    user_id = _UserId.generate()
    user = _User(user_id)

    assert repo.get(user_id) is None

    repo.add(user)
    assert repo.get(user_id) == user

    repo.remove(user)
    assert repo.get(user_id) is None
