"""Tests for app/domain/user/repository.py.

Mirrors `tests/domain/shared_kernel/test_repository.py`'s shape: the
behavior under test is really the shared kernel's `Repository` abstractness,
exercised here through the concrete `UserRepository`/`User` pairing to prove
the interface is actually usable for this aggregate, not just abstract.
"""

import pytest

from app.domain.user.identifiers import UserId
from app.domain.user.repository import UserRepository
from app.domain.user.user import User
from app.domain.user.value_objects import AuthMethod, Locale, Timezone
from tests.domain.user.factories import a_fixed_clock


@pytest.mark.unit
def test_user_repository_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        UserRepository()  # type: ignore[abstract]


@pytest.mark.unit
def test_a_complete_in_memory_implementation_is_usable() -> None:
    class _InMemoryUserRepository(UserRepository):
        def __init__(self) -> None:
            self._users: dict[UserId, User] = {}

        def get(self, entity_id: UserId) -> User | None:
            return self._users.get(entity_id)

        def add(self, aggregate: User) -> None:
            self._users[aggregate.id] = aggregate

        def remove(self, aggregate: User) -> None:
            del self._users[aggregate.id]

    repo = _InMemoryUserRepository()
    user = User.register(
        user_id=UserId.generate(),
        locale=Locale("en"),
        timezone=Timezone("UTC"),
        auth_method=AuthMethod("webauthn_passkey"),
        clock=a_fixed_clock(),
    )

    assert repo.get(user.id) is None

    repo.add(user)
    assert repo.get(user.id) == user

    repo.remove(user)
    assert repo.get(user.id) is None
