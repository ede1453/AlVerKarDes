"""subscriptions table (BILL-001 -- FREE/PREMIUM tier state per user)

Revision ID: 0020_subscriptions
Revises: 0019_notification_preferences
Create Date: 2026-07-20
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0020_subscriptions"
down_revision = "0019_notification_preferences"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "subscriptions",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        # Plain VARCHAR, not a native Postgres enum -- see db_models.py comment.
        sa.Column("tier", sa.String(length=20), nullable=False, server_default="FREE"),
        sa.Column("provider_reference", sa.String(length=200), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # BILL-001: every EXISTING user is explicitly backfilled to FREE here --
    # not left to application-layer "missing row = FREE" defaulting, so no
    # pre-existing user is ever in an ambiguous state after this migration
    # runs ("kayipsiz" requirement). This is a genuine data backfill because
    # subscriptions is a separate table (not a column on users).
    op.execute(
        "INSERT INTO subscriptions (user_id, tier, updated_at) "
        "SELECT id, 'FREE', now() FROM users"
    )


def downgrade() -> None:
    op.drop_table("subscriptions")
