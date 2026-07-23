"""notification_outbox_items table (SCALE-007 Part 1 -- notification_outbox's
real message queue moved from in-memory to Postgres, atomic claim via
SELECT FOR UPDATE SKIP LOCKED. SCALE-002 only moved the leader-election
lock; this is the queue itself.)

Revision ID: 0024_notification_outbox_items
Revises: 0023_provider_schedules
Create Date: 2026-07-23
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0024_notification_outbox_items"
down_revision = "0023_provider_schedules"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notification_outbox_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("channel", sa.String(), nullable=False, server_default="in_app"),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default="{}"),
        # Plain VARCHAR, not a native Postgres enum -- see db_models.py comment.
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("provider", sa.String(), nullable=False, server_default="mock"),
        sa.Column("idempotency_key", sa.String(), nullable=True),
        sa.Column("snoozed_until", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("locked_by", sa.String(), nullable=True),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
    )
    # Supports claim_next()'s WHERE status='PENDING' OR (status='PROCESSING'
    # AND locked_at < stale_cutoff) ORDER BY created_at scan.
    op.create_index(
        "ix_notification_outbox_items_status_created_at",
        "notification_outbox_items",
        ["status", "created_at"],
    )
    # Supports list_due_retries()'s WHERE status='FAILED' AND
    # next_retry_at <= now() scan.
    op.create_index(
        "ix_notification_outbox_items_status_next_retry_at",
        "notification_outbox_items",
        ["status", "next_retry_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_notification_outbox_items_status_next_retry_at",
        table_name="notification_outbox_items",
    )
    op.drop_index(
        "ix_notification_outbox_items_status_created_at",
        table_name="notification_outbox_items",
    )
    op.drop_table("notification_outbox_items")
