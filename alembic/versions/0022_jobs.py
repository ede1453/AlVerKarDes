"""jobs table (SCALE-003 -- job_queue moved from in-memory to Postgres,
atomic claim via SELECT FOR UPDATE SKIP LOCKED)

Revision ID: 0022_jobs
Revises: 0021_products_canonical_key_not_null
Create Date: 2026-07-23
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0022_jobs"
down_revision = "0021_products_canonical_key_not_null"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_type", sa.String(), nullable=False),
        # Plain VARCHAR, not a native Postgres enum -- see db_models.py comment.
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("result", postgresql.JSONB(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("locked_by", sa.String(), nullable=True),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    # Supports claim_next()'s WHERE (status='PENDING' OR (status='RUNNING'
    # AND locked_at < stale_cutoff)) ORDER BY created_at scan.
    op.create_index("ix_jobs_status_created_at", "jobs", ["status", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_jobs_status_created_at", table_name="jobs")
    op.drop_table("jobs")
