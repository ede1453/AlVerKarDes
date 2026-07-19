"""decision_memory owner (AUTH-006 Parça 1, ADR-005)

Revision ID: 0017_decision_memory_owner
Revises: 0016_user_roles
Create Date: 2026-07-19
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0017_decision_memory_owner"
down_revision = "0016_user_roles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Nullable, not NOT NULL -- see ADR-005. The table currently has 0 rows
    # (verified before writing this migration), so NOT NULL would technically
    # be safe today, but whether user_id becomes API-required is a separate
    # decision (Pydantic schema change in AUTH-006 Part 2), independent of
    # this schema change.
    op.add_column(
        "decision_memory",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_decision_memory_user_id",
        "decision_memory",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_decision_memory_user_id", table_name="decision_memory")
    op.drop_column("decision_memory", "user_id")
