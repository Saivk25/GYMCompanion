"""`BcryptPasswordHasher`: the bcrypt-backed implementation of
`app.domain.auth.ports.PasswordHasher`.

bcrypt, not a faster general-purpose hash (SHA-256, ...) — password
hashing specifically wants to be slow and memory-light-but-tunable, so
that brute-forcing a stolen hash table stays expensive even as
commodity hardware gets faster; that's the entire reason a dedicated
password-hashing algorithm exists instead of just hashing with
whatever's already imported elsewhere in the stack.
"""

from __future__ import annotations

import bcrypt

from app.domain.auth.ports import PasswordHasher
from app.domain.auth.value_objects import PasswordHash


class BcryptPasswordHasher(PasswordHasher):
    """Hashes and verifies passwords via the `bcrypt` library. Stateless
    and cheap to construct — safe to build fresh per `Container.handler()`
    call, though `Container` itself holds one shared instance (see
    `app/composition/container.py`) since nothing here is per-request
    state.
    """

    def hash(self, plain_password: str) -> PasswordHash:
        encoded = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())
        return PasswordHash(encoded.decode("utf-8"))

    def verify(self, plain_password: str, password_hash: PasswordHash) -> bool:
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"), password_hash.value.encode("utf-8")
            )
        except ValueError:
            # A malformed stored hash (never produced by hash() itself,
            # but not impossible to end up with via a bad migration or
            # manual data edit) — treated the same as "does not match"
            # rather than propagating, matching this method's documented
            # "never raises on a mismatch" contract.
            return False
