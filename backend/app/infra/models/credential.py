"""`CredentialRow`: persistence row for the `Credential` aggregate.

Deliberately **no row-level security** — the one other table in this
package (besides `exercises`) that breaks the "every table gets RLS"
convention, for a reason specific to this table rather than
`exercises`'s "no tenant to isolate" reasoning: `Credential` is looked
up by *email*, not by id, at the one moment (`POST /login`) where no
tenant identity exists yet to scope the query to — the same
chicken-and-egg gap `app/infra/repositories/workout_repository.py`'s
module docstring names for every other tenant-scoped aggregate's
`get()`, except here it is unsolvable rather than merely awkward:
`users` (the tenant root) can open `tenant_scope` from the very id it
was asked to fetch, but a login attempt supplies no id at all, only an
email — there is nothing to scope to until *after* the row is found.
An RLS policy shaped like every other per-user table's (`USING
(user_id::text = current_setting('app.current_user_id', true))`) would
make every login attempt find zero rows, unconditionally, since
`app.current_user_id` cannot be set before the very lookup that would
establish it. See
`docs/adr/0032-authentication-and-authorization.md` for the full
reasoning and the mitigations that stand in for RLS here instead
(strict 1:1 id-keyed lookups, a unique constraint on `email`, no
"list all credentials" query anywhere in this codebase).
"""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TIMESTAMP, Integer, Uuid

from app.infra.orm_base import Base

_ROLES = ("member",)


class CredentialRow(Base):
    """Persistence row for the `Credential` aggregate — one row per
    `User`, keyed by the same `user_id`. See
    `app/infra/repositories/credential_repository.py` for the
    translation to/from `app.domain.auth.Credential`.
    """

    __tablename__ = "credentials"
    __table_args__ = (
        CheckConstraint(f"role IN {_ROLES}", name="valid_role"),
        CheckConstraint("token_version >= 0", name="non_negative_token_version"),
        UniqueConstraint("email", name="uq_credentials_email"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.user_id"), primary_key=True
    )
    email: Mapped[str] = mapped_column(nullable=False)
    password_hash: Mapped[str] = mapped_column(nullable=False)
    role: Mapped[str] = mapped_column(nullable=False, server_default="member")
    token_version: Mapped[int] = mapped_column(Integer(), nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
