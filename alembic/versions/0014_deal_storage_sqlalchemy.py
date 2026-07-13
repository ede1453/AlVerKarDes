"""deal storage sqlalchemy foundation

Revision ID: 0014_deal_storage_sqlalchemy
Revises: 0013_deal_persistence_recovery
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0014_deal_storage_sqlalchemy"
down_revision = "0013_deal_persistence_recovery"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "deal_storage_records",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            primary_key=True,
        ),
        sa.Column(
            "deal_id",
            sa.String(120),
            nullable=False,
            unique=True,
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
        ),
    )
    op.create_index(
        "ix_deal_storage_records_deal_id",
        "deal_storage_records",
        ["deal_id"],
        unique=True,
    )

    op.create_table(
        "deal_storage_outbox_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            primary_key=True,
        ),
        sa.Column(
            "aggregate_type",
            sa.String(80),
            nullable=False,
        ),
        sa.Column(
            "aggregate_id",
            sa.String(120),
            nullable=False,
        ),
        sa.Column(
            "event_type",
            sa.String(120),
            nullable=False,
        ),
        sa.Column(
            "payload",
            postgresql.JSONB(),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(30),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "published_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_deal_storage_outbox_status",
        "deal_storage_outbox_events",
        ["status"],
        unique=False,
    )

    op.create_table(
        "deal_storage_integrity_reports",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            primary_key=True,
        ),
        sa.Column(
            "healthy",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "record_count",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "issue_count",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "issues",
            postgresql.JSONB(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
    )

    op.create_table(
        "deal_storage_backup_manifests",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            primary_key=True,
        ),
        sa.Column(
            "backup_name",
            sa.String(255),
            nullable=False,
        ),
        sa.Column(
            "record_count",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "manifest_payload",
            postgresql.JSONB(),
            nullable=False,
        ),
        sa.Column(
            "manifest_hash",
            sa.String(64),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "backup_name",
            "manifest_hash",
            name="uq_deal_storage_backup_manifest",
        ),
    )


def downgrade() -> None:
    op.drop_table(
        "deal_storage_backup_manifests"
    )
    op.drop_table(
        "deal_storage_integrity_reports"
    )
    op.drop_index(
        "ix_deal_storage_outbox_status",
        table_name="deal_storage_outbox_events",
    )
    op.drop_table(
        "deal_storage_outbox_events"
    )
    op.drop_index(
        "ix_deal_storage_records_deal_id",
        table_name="deal_storage_records",
    )
    op.drop_table(
        "deal_storage_records"
    )
