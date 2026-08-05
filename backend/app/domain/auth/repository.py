"""The persistence contract for the `Credential` aggregate.

Adds exactly one method beyond the shared kernel's `Repository[TAggregate,
TId]` (`get`/`add`/`remove`): `get_by_email`, needed by `POST /login`
(look up a credential by the email the caller typed, not by an id it
doesn't have yet) — a real, concrete, immediate caller, matching
`app.domain.user.repository`'s own documented standard ("add a method
here only once a concrete caller needs it, not speculatively").

Email uniqueness (two credentials can't share one email) is enforced by
a database unique constraint plus `app/infra/repositories/
credential_repository.py` translating the resulting integrity error into
an `ApplicationResult` failure — not by this domain layer, the same split
already documented for `Goal`'s "one per day" note in
`app.domain.readiness.readiness`: the domain layer doesn't reach across
the whole `credentials` table to check a sibling record; that is an
application/repository-layer concern.
"""

from __future__ import annotations

from abc import abstractmethod

from app.domain.auth.credential import Credential
from app.domain.auth.value_objects import Email
from app.domain.shared_kernel.repository import Repository
from app.domain.user.identifiers import UserId


class CredentialRepository(Repository[Credential, UserId]):
    """Persistence contract for the `Credential` aggregate. See the
    module docstring for why it declares one method beyond the shared
    kernel's. `app/infra/` provides the real, Postgres-backed
    implementation.
    """

    @abstractmethod
    def get_by_email(self, email: Email) -> Credential | None:
        """Returns the credential registered under `email`, or `None`
        if no such credential exists. Not finding one is an expected
        outcome (a login attempt with an unregistered email), not an
        error — matching `Repository.get()`'s own documented
        convention."""
        raise NotImplementedError  # pragma: no cover — abstract, always overridden
