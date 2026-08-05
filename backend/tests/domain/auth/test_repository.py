"""Tests for app/domain/auth/repository.py.

Mirrors `tests/domain/user/test_repository.py`'s shape: the behavior
under test is really the shared kernel's `Repository` abstractness (plus
this one's extra `get_by_email`), exercised through a minimal in-memory
implementation to prove the interface is actually usable, not just
abstract.
"""

import pytest

from app.domain.auth.credential import Credential
from app.domain.auth.repository import CredentialRepository
from app.domain.auth.value_objects import Email, PasswordHash
from app.domain.user.identifiers import UserId
from tests.domain.auth.factories import a_fixed_clock


@pytest.mark.unit
def test_credential_repository_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        CredentialRepository()  # type: ignore[abstract]


@pytest.mark.unit
def test_a_complete_in_memory_implementation_is_usable() -> None:
    class _InMemoryCredentialRepository(CredentialRepository):
        def __init__(self) -> None:
            self._by_id: dict[UserId, Credential] = {}

        def get(self, entity_id: UserId) -> Credential | None:
            return self._by_id.get(entity_id)

        def add(self, aggregate: Credential) -> None:
            self._by_id[aggregate.id] = aggregate

        def remove(self, aggregate: Credential) -> None:
            del self._by_id[aggregate.id]

        def get_by_email(self, email: Email) -> Credential | None:
            return next((c for c in self._by_id.values() if c.email == email), None)

    repo = _InMemoryCredentialRepository()
    credential = Credential.register(
        user_id=UserId.generate(),
        email=Email("sai@example.com"),
        password_hash=PasswordHash("$2b$12$abcdefghijklmnopqrstuv"),
        clock=a_fixed_clock(),
    )

    assert repo.get(credential.id) is None
    assert repo.get_by_email(Email("sai@example.com")) is None

    repo.add(credential)
    assert repo.get(credential.id) == credential
    assert repo.get_by_email(Email("sai@example.com")) == credential
    assert repo.get_by_email(Email("nobody@example.com")) is None

    repo.remove(credential)
    assert repo.get(credential.id) is None


@pytest.mark.unit
def test_subclass_missing_get_by_email_still_cannot_be_instantiated() -> None:
    class _IncompleteRepository(CredentialRepository):
        def get(self, entity_id: UserId) -> Credential | None:
            return None

        def add(self, aggregate: Credential) -> None:
            pass

        def remove(self, aggregate: Credential) -> None:
            pass

        # get_by_email() deliberately not implemented

    with pytest.raises(TypeError):
        _IncompleteRepository()  # type: ignore[abstract]
