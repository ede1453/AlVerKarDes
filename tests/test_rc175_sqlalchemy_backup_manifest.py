from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.domains.deal_storage.sqlalchemy_models import DealStorageBase
from app.domains.deal_storage.sqlalchemy_repository import SQLAlchemyDealStorageRepository


def test_rc175_backup_manifest_verify():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    DealStorageBase.metadata.create_all(engine)
    repo = SQLAlchemyDealStorageRepository(Session(engine))

    repo.upsert_record(
        deal_id="deal-1",
        payload={"status":"VALIDATED"},
    )
    repo.session.commit()

    manifest = repo.create_backup_manifest(
        backup_name="daily"
    )
    result = repo.verify_backup_manifest(
        manifest["manifest_id"]
    )

    assert manifest["record_count"] == 1
    assert result["verified"] is True
