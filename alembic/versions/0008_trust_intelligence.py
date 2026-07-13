"""trust intelligence

Revision ID: 0008_trust_intelligence
Revises: 0007_feedback_learning
Create Date: 2026-07-05
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0008_trust_intelligence"
down_revision = "0007_feedback_learning"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "trust_signals",
        sa.Column("source_type", sa.String(), primary_key=True),
        sa.Column("source_id", sa.String(), primary_key=True),
        sa.Column("positive_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("negative_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("neutral_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("fraud_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("return_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_count", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "trust_profiles",
        sa.Column("entity_type", sa.String(), primary_key=True),
        sa.Column("entity_id", sa.String(), primary_key=True),
        sa.Column("trust_score", sa.Integer(), nullable=False),
        sa.Column("reliability_score", sa.Integer(), nullable=False),
        sa.Column("positive_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("negative_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("fraud_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_updated", sa.DateTime(timezone=True), nullable=False),
        sa.Column("trust_payload", postgresql.JSONB(), nullable=False, server_default="{}"),
    )


def downgrade():
    op.drop_table("trust_profiles")
    op.drop_table("trust_signals")
