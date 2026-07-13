"""llm audit prompt version

Revision ID: 0010_llm_audit_prompt_version
Revises: 0009_llm_audit_traces
Create Date: 2026-07-05
"""

from alembic import op
import sqlalchemy as sa


revision = "0010_llm_audit_prompt_version"
down_revision = "0009_llm_audit_traces"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "llm_audit_traces",
        sa.Column("prompt_version", sa.String(), nullable=False, server_default="shopping_v1"),
    )


def downgrade():
    op.drop_column("llm_audit_traces", "prompt_version")
