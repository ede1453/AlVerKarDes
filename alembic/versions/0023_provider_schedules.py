"""provider_schedules table (SCALE-004 -- provider_scheduler moved from
in-memory to Postgres, atomic due-claim via SELECT FOR UPDATE SKIP LOCKED)

Revision ID: 0023_provider_schedules
Revises: 0022_jobs
Create Date: 2026-07-23
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0023_provider_schedules"
down_revision = "0022_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "provider_schedules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("providers", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("interval_seconds", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        # Plain VARCHAR, not a native Postgres enum -- see db_models.py comment.
        sa.Column("status", sa.String(length=20), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_result", postgresql.JSONB(), nullable=True),
        sa.Column("locked_by", sa.String(), nullable=True),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
    )
    # Supports claim()'s WHERE enabled=true AND (status='ACTIVE' OR
    # (status='RUNNING' AND locked_at < stale_cutoff)) scan for due schedules.
    op.create_index(
        "ix_provider_schedules_enabled_status",
        "provider_schedules",
        ["enabled", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_provider_schedules_enabled_status", table_name="provider_schedules")
    op.drop_table("provider_schedules")
