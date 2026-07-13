"""decision memory

Revision ID: 0005_decision_memory
Revises: 0004_merge_candidates
Create Date: 2026-07-05
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0005_decision_memory"
down_revision = "0004_merge_candidates"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "decision_memory",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("product_id", sa.String(), nullable=True),
        sa.Column("offer_id", sa.String(), nullable=True),
        sa.Column("country", sa.String(), nullable=False, server_default="DE"),
        sa.Column("final_decision", sa.String(), nullable=False),
        sa.Column("confidence", sa.Integer(), nullable=False),
        sa.Column("risk_level", sa.String(), nullable=True),
        sa.Column("opportunity_level", sa.String(), nullable=True),
        sa.Column("deal_score", sa.Integer(), nullable=True),
        sa.Column("authenticity_score", sa.Integer(), nullable=True),
        sa.Column("recommendation", sa.String(), nullable=True),
        sa.Column("reason_codes", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("decision_context", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("outcome", postgresql.JSONB(), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade():
    op.drop_table("decision_memory")
