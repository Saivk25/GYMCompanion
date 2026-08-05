"""create credentials table

Revision ID: a1c3e7f92b4d
Revises: f85a28bb5661
Create Date: 2026-08-05 03:00:00.000000

The table shape was hand-written from `app/infra/models/credential.py`
(`CredentialRow`), the same starting point every migration in this
series uses (see the users-table migration's own docstring) since no
live database is reachable in this environment to run `alembic
revision --autogenerate` against.

**Deliberately no row-level security** — see
`app/infra/models/credential.py`'s module docstring for the full
reasoning: `credentials` is looked up by email at login, before any
tenant identity exists to scope the query to, so an RLS policy shaped
like every other per-user table's would make login itself impossible.
This is the second table in the schema (after `exercises`) that does
not get `ENABLE`/`FORCE ROW LEVEL SECURITY`, for a different reason
than `exercises`'s "no tenant to isolate" — here there *is* a tenant
(`user_id`, foreign-keyed to `users`), it just cannot be known before
this table's own lookup resolves it.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1c3e7f92b4d"
down_revision: str | Sequence[str] | None = "f85a28bb5661"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "credentials",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("role", sa.String(), server_default="member", nullable=False),
        sa.Column("token_version", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.CheckConstraint("role IN ('member')", name=op.f("ck_credentials_valid_role")),
        sa.CheckConstraint(
            "token_version >= 0", name=op.f("ck_credentials_non_negative_token_version")
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.user_id"], name=op.f("fk_credentials_user_id_users")
        ),
        sa.PrimaryKeyConstraint("user_id", name=op.f("pk_credentials")),
        sa.UniqueConstraint("email", name="uq_credentials_email"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("credentials")
