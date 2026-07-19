"""watchlist_items table (CLIENT-002e -- watchlist moved from in-memory to Postgres)

Revision ID: 0018_watchlist_items
Revises: 0017_decision_memory_owner
Create Date: 2026-07-19
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0018_watchlist_items"
down_revision = "0017_decision_memory_owner"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "watchlist_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("product_key", sa.String(), nullable=False),
        sa.Column("query", sa.String(), nullable=False),
        sa.Column("target_price", sa.String(), nullable=True),
        sa.Column("marketplaces", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("channels", postgresql.JSONB(), nullable=False, server_default="[]"),
        # Plain VARCHAR, not a native Postgres enum -- see db_models.py comment.
        sa.Column("status", sa.String(length=20), nullable=False, server_default="ACTIVE"),
        sa.Column("last_evaluation", postgresql.JSONB(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_watchlist_items_user_id", "watchlist_items", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_watchlist_items_user_id", table_name="watchlist_items")
    op.drop_table("watchlist_items")
