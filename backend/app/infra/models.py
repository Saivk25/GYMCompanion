"""SQLAlchemy ORM models: the persistence shape of each aggregate.

These are infra-layer mapping classes, not the Domain Core. They exist so
Alembic has something to diff against and so `app/infra` repositories have
a concrete row shape to read/write. The framework-free business entity for
each aggregate (validation rules, lifecycle transitions, business rules —
see the Domain Model & Decision Engine Bible, Section 4) is built in
Sprint 1, Step 12 and lives in `app/domain`; repositories translate between
the two. Nothing here should ever be imported by `app/domain`.

`UserAccount` maps the User / Account aggregate (Domain Model Bible,
Section 4.1) using its frozen key attributes verbatim: user_id, created_at,
locale, timezone, account_status, auth_method. `account_status` is
constrained at the database level to the aggregate's five lifecycle states
(Invited -> Active -> Suspended (optional) -> Deleted (soft) -> Purged
(hard)) as a data-integrity backstop; enforcing the *transition rules*
between those states (e.g. "one-directional except Suspended -> Active")
is the Domain Core's job (Step 12), not a database constraint's.

Row-level security for this table is enabled and enforced by the migration
that creates it (`alembic/versions/`), not by anything in this file —
SQLAlchemy has no concept of RLS policies, so it is applied as raw SQL in
the migration and documented there.
"""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TIMESTAMP, Uuid

from app.infra.orm_base import Base

_ACCOUNT_STATUSES = ("invited", "active", "suspended", "deleted", "purged")


class UserAccount(Base):
    """Persistence row for the User / Account aggregate's root identity.

    Creating a row (signup): generate `user_id` in application code and
    call `tenant_scope(session, str(user_id))` *before* adding/committing
    this object — do not rely on the column's `gen_random_uuid()` default
    and insert without a tenant scope already set. The table's RLS policy
    allows the bare INSERT either way, but a normal ORM insert also reads
    the new row back (to populate `created_at`/`account_status` from their
    server defaults), and that read is governed by the same policy's
    `USING` clause — which only matches once `app.current_user_id` is
    already the row's own id. See the creating migration
    (`alembic/versions/..._create_users_table_with_row_level_.py`) for the
    full explanation of why, verified against a real database.
    """

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            f"account_status IN {_ACCOUNT_STATUSES}",
            name="valid_account_status",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    locale: Mapped[str] = mapped_column(nullable=False)
    timezone: Mapped[str] = mapped_column(nullable=False)
    account_status: Mapped[str] = mapped_column(nullable=False, server_default="invited")
    auth_method: Mapped[str] = mapped_column(nullable=False)
