"""Immutable value objects owned by the `Credential` aggregate.

Same discipline as `app.domain.user.value_objects`: every type here is a
`ValueObject` subclass, validated once at construction so an instance is
either fully valid or doesn't exist.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.domain.shared_kernel.validation import ensure, ensure_not_empty
from app.domain.shared_kernel.value_object import ValueObject

# A permissive, structural check ("something@something.something"), not a
# full RFC 5321 parser — domain code needs to reject obvious garbage ("not
# an email"), the same "permissive check, not a full parser" reasoning
# `app.domain.user.value_objects._LOCALE_PATTERN` already documents for
# BCP-47 tags. A real email-validation library (DNS/MX lookups, the full
# RFC grammar) would be exactly the kind of dependency app/domain is not
# allowed to take on (see test_import_boundaries.py); the API layer or a
# future email-verification flow is where deeper validation belongs.
_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True)
class Email(ValueObject):
    """A login identity's email address, e.g. `Email("sai@example.com")`.

    Normalized to lowercase and stripped of surrounding whitespace at
    construction — two `Email` instances that differ only by case or
    incidental whitespace must compare equal and collide on the same
    `CredentialRepository.get_by_email()` lookup, matching how every real
    mail provider treats the domain part (and, in practice, the local
    part too, for this app's own registration flow) case-insensitively.
    Uniqueness itself is *not* enforced here — see
    `app.domain.auth.repository`'s module docstring for why that is an
    application/repository-layer concern, the same split
    `app.domain.readiness.readiness` already documents for "one
    check-in per day."
    """

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()
        ensure_not_empty(normalized, "email")
        ensure(
            _EMAIL_PATTERN.fullmatch(normalized) is not None,
            f"email must look like 'name@example.com', got {self.value!r}",
        )
        object.__setattr__(self, "value", normalized)


@dataclass(frozen=True)
class PasswordHash(ValueObject):
    """An opaque, already-hashed password — never a plaintext password.

    This wrapper's only invariant is "it must actually name something";
    it does not know or care which hashing algorithm produced it, how
    many rounds it used, or how to verify a plaintext password against
    it — that is `app.domain.auth.ports.PasswordHasher`'s job, kept
    deliberately out of the domain layer so no hashing library (bcrypt,
    argon2, ...) is ever imported here. Constructing a `PasswordHash`
    directly from a plaintext password is a caller bug this type cannot
    detect; only `PasswordHasher.hash()` should ever produce one.
    """

    value: str

    def __post_init__(self) -> None:
        ensure_not_empty(self.value, "password_hash")
