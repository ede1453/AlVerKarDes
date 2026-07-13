"""user preference profiles

Revision ID: 0006_user_preference_profiles
Revises: 0005_decision_memory
Create Date: 2026-07-05
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0006_user_preference_profiles"
down_revision = "0005_decision_memory"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_preference_profiles",
        sa.Column("user_id", sa.String(), primary_key=True),
        sa.Column("preferred_brands", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("avoided_brands", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("preferred_categories", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("price_sensitivity", sa.String(), nullable=False, server_default="MEDIUM"),
        sa.Column("minimum_confidence", sa.Integer(), nullable=False, server_default="70"),
    )


def downgrade():
    op.drop_table("user_preference_profiles")
