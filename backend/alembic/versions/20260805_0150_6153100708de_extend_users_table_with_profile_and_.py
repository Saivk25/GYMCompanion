"""extend users table with profile and preferences

Revision ID: 6153100708de
Revises: e1be8b00d81f
Create Date: 2026-08-05 01:50:26.290351

Adds the columns `app/infra/models/user.py`'s extension of `UserAccount`
introduced for `UserProfile`/`UserPreferences` (Sprint 2's growth of the
`User` aggregate, never brought back in sync with this table until now —
see that module's own docstring). No row-level security changes: `users`
already has `ENABLE`/`FORCE ROW LEVEL SECURITY` plus its tenant-isolation
policy from the table's creating migration, and every column added here is
just more data on the same already-RLS-protected row — nothing here
introduces a new table or a new tenant boundary to guard.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6153100708de"
down_revision: str | Sequence[str] | None = "e1be8b00d81f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("users", sa.Column("height_cm", sa.Float(), nullable=True))
    op.add_column("users", sa.Column("birth_year", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("experience_level", sa.String(), nullable=True))
    op.add_column("users", sa.Column("biological_sex", sa.String(), nullable=True))
    op.add_column("users", sa.Column("quiet_hours_starts_at", sa.Time(), nullable=True))
    op.add_column("users", sa.Column("quiet_hours_ends_at", sa.Time(), nullable=True))
    op.add_column(
        "users",
        sa.Column(
            "biometric_app_lock_enabled", sa.Boolean(), server_default="false", nullable=False
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "available_equipment", sa.ARRAY(sa.String()), server_default="{}", nullable=False
        ),
    )
    op.create_check_constraint(
        op.f("ck_users_valid_experience_level"),
        "users",
        "experience_level IS NULL OR experience_level IN ('beginner', 'intermediate', 'advanced')",
    )
    op.create_check_constraint(
        op.f("ck_users_valid_biological_sex"),
        "users",
        "biological_sex IS NULL OR biological_sex IN ('female', 'male')",
    )
    op.create_check_constraint(
        op.f("ck_users_profile_all_or_none"),
        "users",
        "(height_cm IS NULL AND birth_year IS NULL AND experience_level IS NULL) "
        "OR (height_cm IS NOT NULL AND birth_year IS NOT NULL "
        "AND experience_level IS NOT NULL)",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(op.f("ck_users_profile_all_or_none"), "users", type_="check")
    op.drop_constraint(op.f("ck_users_valid_biological_sex"), "users", type_="check")
    op.drop_constraint(op.f("ck_users_valid_experience_level"), "users", type_="check")
    op.drop_column("users", "available_equipment")
    op.drop_column("users", "biometric_app_lock_enabled")
    op.drop_column("users", "quiet_hours_ends_at")
    op.drop_column("users", "quiet_hours_starts_at")
    op.drop_column("users", "biological_sex")
    op.drop_column("users", "experience_level")
    op.drop_column("users", "birth_year")
    op.drop_column("users", "height_cm")
