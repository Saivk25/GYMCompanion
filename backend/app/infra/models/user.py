"""`UserAccount`: persistence row for the User aggregate.

Extends the Sprint 1 scaffolding (columns for `user_id`/`created_at`/
`locale`/`timezone`/`account_status`/`auth_method` only) with the
`UserProfile`/`UserPreferences` value objects `app.domain.user.User`
gained in Sprint 2 — this table predates that growth and had never been
brought back in sync with the aggregate's current shape until now. See
`docs/adr/0029-persistence-layer.md`.

`UserProfile` is all-or-nothing on the aggregate (`profile: UserProfile |
None` — never partially filled, see that class's own docstring), so its
three required columns (`height_cm`, `birth_year`, `experience_level`)
carry a matching CHECK constraint: either all three are `NULL` together
(no profile) or all three are set together (a complete profile).
`biological_sex` is excluded from that constraint because it is optional
even *within* a complete `UserProfile` (`sex: BiologicalSex | None`).

`UserPreferences` is never `None` on the aggregate (`User.__init__`
defaults it to `UserPreferences()`), so its columns are never all-`NULL`
by convention, though the schema does not need a constraint to express
that — an absent value simply reads back as the same defaults
`UserPreferences()` already provides.
"""

import uuid
from datetime import datetime, time

from sqlalchemy import ARRAY, CheckConstraint, String, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TIMESTAMP, Time, Uuid

from app.infra.orm_base import Base

_ACCOUNT_STATUSES = ("invited", "active", "suspended", "deleted", "purged")
_EXPERIENCE_LEVELS = ("beginner", "intermediate", "advanced")
_BIOLOGICAL_SEXES = ("female", "male")


class UserAccount(Base):
    """Persistence row for the User / Account aggregate root, its
    optional `UserProfile`, and its always-present `UserPreferences`.

    See `app/infra/repositories/user_repository.py` for the translation
    to/from `app.domain.user.User`, and the original creating migration's
    docstring (`alembic/versions/..._create_users_table_with_row_level_
    .py`) for the tenant-scoping insert pattern every write to this table
    must still follow — unchanged by this extension.
    """

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            f"account_status IN {_ACCOUNT_STATUSES}",
            name="valid_account_status",
        ),
        CheckConstraint(
            f"experience_level IS NULL OR experience_level IN {_EXPERIENCE_LEVELS}",
            name="valid_experience_level",
        ),
        CheckConstraint(
            f"biological_sex IS NULL OR biological_sex IN {_BIOLOGICAL_SEXES}",
            name="valid_biological_sex",
        ),
        CheckConstraint(
            "(height_cm IS NULL AND birth_year IS NULL AND experience_level IS NULL) "
            "OR (height_cm IS NOT NULL AND birth_year IS NOT NULL "
            "AND experience_level IS NOT NULL)",
            name="profile_all_or_none",
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

    # UserProfile (optional, all-or-nothing except biological_sex — see
    # the module docstring).
    height_cm: Mapped[float | None] = mapped_column(nullable=True)
    birth_year: Mapped[int | None] = mapped_column(nullable=True)
    experience_level: Mapped[str | None] = mapped_column(nullable=True)
    biological_sex: Mapped[str | None] = mapped_column(nullable=True)

    # UserPreferences (always present on the aggregate; columns default
    # to what UserPreferences() itself defaults to).
    quiet_hours_starts_at: Mapped[time | None] = mapped_column(Time(), nullable=True)
    quiet_hours_ends_at: Mapped[time | None] = mapped_column(Time(), nullable=True)
    biometric_app_lock_enabled: Mapped[bool] = mapped_column(nullable=False, server_default="false")
    available_equipment: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, server_default="{}"
    )
