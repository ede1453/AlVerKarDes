"""alert rules

Revision ID: 0002_alert_rules
Revises: 0001_initial_stabilized
Create Date: 2026-07-05
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0002_alert_rules"
down_revision = "0001_initial_stabilized"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "alert_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("offer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("offers.id"), nullable=False),
        sa.Column("rule_type", sa.String(length=50), nullable=False),
        sa.Column("target_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("drop_percent_threshold", sa.Numeric(6, 2), nullable=True),
        sa.Column("notify_on_back_in_stock", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_alert_rules_offer_active", "alert_rules", ["offer_id", "is_active"])


def downgrade():
    op.drop_index("ix_alert_rules_offer_active", table_name="alert_rules")
    op.drop_table("alert_rules")
