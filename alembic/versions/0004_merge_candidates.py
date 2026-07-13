"""merge candidates

Revision ID: 0004_merge_candidates
Revises: 0003_pending_notifications
Create Date: 2026-07-05
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0004_merge_candidates"
down_revision = "0003_pending_notifications"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "merge_candidates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("signature", sa.String(length=500), nullable=False),
        sa.Column("master_title", sa.Text(), nullable=False),
        sa.Column("offer_count", sa.Integer(), nullable=False),
        sa.Column("average_confidence", sa.Float(), nullable=False),
        sa.Column("decision", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="PENDING"),
        sa.Column("offer_titles_json", postgresql.JSONB(), nullable=False),
        sa.Column("sources_json", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_merge_candidates_signature", "merge_candidates", ["signature"])
    op.create_index("ix_merge_candidates_decision", "merge_candidates", ["decision"])
    op.create_index("ix_merge_candidates_status", "merge_candidates", ["status"])


def downgrade():
    op.drop_index("ix_merge_candidates_status", table_name="merge_candidates")
    op.drop_index("ix_merge_candidates_decision", table_name="merge_candidates")
    op.drop_index("ix_merge_candidates_signature", table_name="merge_candidates")
    op.drop_table("merge_candidates")
