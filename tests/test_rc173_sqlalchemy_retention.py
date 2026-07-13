from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.domains.deal_storage.sqlalchemy_models import DealStorageBase
from app.domains.deal_storage.sqlalchemy_repository import SQLAlchemyDealStorageRepository


def test_rc173_database_retention_purge():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    DealStorageBase.metadata.create_all(engine)
    repo = SQLAlchemyDealStorageRepository(Session(engine))

    repo.upsert_record(
        deal_id="old-deal",
        payload={"status":"ARCHIVED"},
        archived=True,
    )
    record = repo.session.scalar(
        __import__("sqlalchemy").select(
            __import__(
                "app.domains.deal_storage.sqlalchemy_models",
                fromlist=["DealStorageRecord"],
            ).DealStorageRecord
        )
    )
    record.persisted_at = datetime(
        2025, 1, 1, tzinfo=timezone.utc
    )
    repo.session.commit()

    result = repo.purge_archived(
        older_than_days=30,
        reference_time=datetime(
            2026, 7, 12, tzinfo=timezone.utc
        ),
        dry_run=False,
    )
    assert result["purged_count"] == 1
    assert repo.get_record("old-deal") is None
