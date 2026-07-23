"""user_profiles table (SCALE-008 -- user_profiles moved from in-memory to
Postgres. Fixes two boxes: (1) each worker's own dict meant a preference
saved on one worker was invisible to another worker's
profile_aware_recommendations read -- silent recommendation-quality loss,
no error raised; (2) apply_preferences()/merge_feedback()'s read-modify-
write was a lost-update race even against a real DB unless the read locks
the row, so this table's access goes through SELECT ... FOR UPDATE.)

Revision ID: 0025_user_profiles
Revises: 0024_notification_outbox_items
Create Date: 2026-07-23
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0025_user_profiles"
down_revision = "0024_notification_outbox_items"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_profiles",
        sa.Column("user_id", sa.String(), primary_key=True),
        sa.Column("preferred_product_keys", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("avoided_product_keys", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("preferred_marketplaces", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("blocked_marketplaces", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("preferred_brands", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("risk_tolerance", sa.String(), nullable=False, server_default="MEDIUM"),
        sa.Column("profile_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("user_profiles")
