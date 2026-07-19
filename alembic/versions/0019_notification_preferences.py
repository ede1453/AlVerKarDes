"""notification_preferences table (CLIENT-002g -- deal-notification
channel/threshold/quiet-hours preferences moved from in-memory to Postgres)

Revision ID: 0019_notification_preferences
Revises: 0018_watchlist_items
Create Date: 2026-07-20
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0019_notification_preferences"
down_revision = "0018_watchlist_items"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notification_preferences",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("enabled_channels", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("minimum_confidence", sa.Float(), nullable=False, server_default="70"),
        sa.Column("minimum_discount_pct", sa.Float(), nullable=False, server_default="10"),
        sa.Column("quiet_hours_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("quiet_hours_start", sa.String(length=5), nullable=False, server_default="22:00"),
        sa.Column("quiet_hours_end", sa.String(length=5), nullable=False, server_default="08:00"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("notification_preferences")
