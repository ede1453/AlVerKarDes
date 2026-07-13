"""deal persistence and recovery

Revision ID: 0013_deal_persistence_recovery
Revises: 0012_commerce_ingestion_persistence
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0013_deal_persistence_recovery"
down_revision = "0012_commerce_ingestion_persistence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "deal_persistence_records",
        sa.Column(
            "deal_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
        ),
        sa.Column(
            "version",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "payload",
            postgresql.JSONB(),
            nullable=False,
        ),
        sa.Column(
            "payload_hash",
            sa.String(64),
            nullable=False,
        ),
        sa.Column(
            "archived",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "persisted_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "deal_snapshots",
        sa.Column(
            "snapshot_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
        ),
        sa.Column(
            "deal_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "record_version",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "snapshot_payload",
            postgresql.JSONB(),
            nullable=False,
        ),
        sa.Column(
            "snapshot_hash",
            sa.String(64),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "deal_checkpoints",
        sa.Column(
            "checkpoint_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
        ),
        sa.Column(
            "deal_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "record_version",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "lifecycle_status",
            sa.String(40),
            nullable=False,
        ),
        sa.Column(
            "decision_version",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "event_cursor",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "deal_archives",
        sa.Column(
            "archive_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
        ),
        sa.Column(
            "deal_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "snapshot_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "reason",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "actor",
            sa.String(255),
            nullable=False,
        ),
        sa.Column(
            "archived_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "deal_recovery_events",
        sa.Column(
            "recovery_event_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
        ),
        sa.Column(
            "deal_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "snapshot_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "restored_version",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("deal_recovery_events")
    op.drop_table("deal_archives")
    op.drop_table("deal_checkpoints")
    op.drop_table("deal_snapshots")
    op.drop_table("deal_persistence_records")
