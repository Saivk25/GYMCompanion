"""`CredentialSqlRepository`: the SQLAlchemy-backed implementation of
`app.domain.auth.repository.CredentialRepository`.

No `tenant_scope` anywhere in this file — see
`app/infra/models/credential.py`'s module docstring for why
`credentials` deliberately carries no row-level security, unlike every
other per-user table in this package.
"""

from __future__ import annotations

from sqlalchemy import select

from app.domain.auth.credential import Credential
from app.domain.auth.enums import Role
from app.domain.auth.repository import CredentialRepository
from app.domain.auth.value_objects import Email, PasswordHash
from app.domain.user.identifiers import UserId
from app.infra.models.credential import CredentialRow
from app.infra.repositories._tracking import TrackingRepository


class CredentialSqlRepository(
    CredentialRepository, TrackingRepository[Credential, UserId, CredentialRow]
):
    """Postgres-backed `CredentialRepository`. See the module docstring
    for why no method here touches `tenant_scope`."""

    def get(self, entity_id: UserId) -> Credential | None:
        row = self._session.get(CredentialRow, entity_id.value)
        if row is None:
            return None
        credential = _to_domain(row)
        self._track(entity_id, credential, row)
        return credential

    def add(self, aggregate: Credential) -> None:
        row = CredentialRow(user_id=aggregate.id.value)
        self._apply_to_row(aggregate, row)
        self._session.add(row)
        self._track(aggregate.id, aggregate, row)

    def remove(self, aggregate: Credential) -> None:
        row = self._session.get(CredentialRow, aggregate.id.value)
        if row is not None:
            self._session.delete(row)
        self._untrack(aggregate.id)

    def get_by_email(self, email: Email) -> Credential | None:
        row = self._session.scalars(
            select(CredentialRow).where(CredentialRow.email == email.value)
        ).first()
        if row is None:
            return None
        credential = _to_domain(row)
        self._track(credential.id, credential, row)
        return credential

    def _apply_to_row(self, aggregate: Credential, row: CredentialRow) -> None:
        row.email = aggregate.email.value
        row.password_hash = aggregate.password_hash.value
        row.role = aggregate.role.value
        row.token_version = aggregate.token_version
        row.created_at = aggregate.created_at


def _to_domain(row: CredentialRow) -> Credential:
    return Credential(
        UserId(row.user_id),
        email=Email(row.email),
        password_hash=PasswordHash(row.password_hash),
        role=Role(row.role),
        token_version=row.token_version,
        created_at=row.created_at,
    )
