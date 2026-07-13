"""llm audit traces

Revision ID: 0009_llm_audit_traces
Revises: 0008_trust_intelligence
Create Date: 2026-07-05
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0009_llm_audit_traces"
down_revision = "0008_trust_intelligence"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "llm_audit_traces",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("assistant_decision", sa.String(), nullable=True),
        sa.Column("prompt_hash", sa.String(length=64), nullable=True),
        sa.Column("safety_warnings", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("usage", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade():
    op.drop_table("llm_audit_traces")
