"""user roles (AUTH-006 Parça 1, ADR-005)

Revision ID: 0016_user_roles
Revises: 0015_authentication_core
Create Date: 2026-07-19
"""

from alembic import op
import sqlalchemy as sa


revision = "0016_user_roles"
down_revision = "0015_authentication_core"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Plain VARCHAR, not a Postgres native ENUM -- see ADR-005 and the
    # matching comment on identity.models.User.status: this codebase already
    # hit asyncpg.exceptions.UndefinedObjectError once from a SQLAlchemy
    # native Enum() column bound against a plain VARCHAR column created by an
    # earlier migration. native_enum=False on the ORM side keeps this in sync
    # deliberately.
    #
    # DEFAULT 'SHOPPER' backfills every existing row in the same statement --
    # no separate data migration/backfill step needed.
    op.add_column(
        "users",
        sa.Column(
            "role",
            sa.String(length=20),
            nullable=False,
            server_default="SHOPPER",
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "role")
