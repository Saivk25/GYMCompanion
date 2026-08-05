"""Tests for app/infra/security/bcrypt_password_hasher.py.

`@pytest.mark.unit`, not `integration` — bcrypt itself needs no
database and is fast enough (a handful of hash/verify calls) to run
with the rest of the unit suite.
"""

import pytest

from app.domain.auth.value_objects import PasswordHash
from app.infra.security.bcrypt_password_hasher import BcryptPasswordHasher


@pytest.mark.unit
def test_verify_succeeds_for_the_correct_password() -> None:
    hasher = BcryptPasswordHasher()
    hashed = hasher.hash("correct horse battery staple")

    assert hasher.verify("correct horse battery staple", hashed) is True


@pytest.mark.unit
def test_verify_fails_for_the_wrong_password() -> None:
    hasher = BcryptPasswordHasher()
    hashed = hasher.hash("correct horse battery staple")

    assert hasher.verify("wrong password", hashed) is False


@pytest.mark.unit
def test_hash_never_stores_the_plaintext() -> None:
    hasher = BcryptPasswordHasher()
    hashed = hasher.hash("correct horse battery staple")

    assert hashed.value != "correct horse battery staple"


@pytest.mark.unit
def test_hashing_the_same_password_twice_produces_different_hashes() -> None:
    """bcrypt salts every hash independently — two hashes of the same
    password must never be byte-identical, or an attacker could spot
    two users sharing a password just by comparing stored hashes."""
    hasher = BcryptPasswordHasher()

    first = hasher.hash("correct horse battery staple")
    second = hasher.hash("correct horse battery staple")

    assert first.value != second.value
    assert hasher.verify("correct horse battery staple", first) is True
    assert hasher.verify("correct horse battery staple", second) is True


@pytest.mark.unit
def test_verify_returns_false_for_a_malformed_stored_hash() -> None:
    """Never raises on a malformed hash — see the class's own
    docstring for why this is treated the same as a mismatch."""
    hasher = BcryptPasswordHasher()

    assert hasher.verify("anything", PasswordHash("not-a-real-bcrypt-hash")) is False
