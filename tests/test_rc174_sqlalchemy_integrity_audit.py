from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.domains.deal_storage.sqlalchemy_models import (
    DealStorageBase,
    DealStorageRecord,
)
from app.domains.deal_storage.sqlalchemy_repository import SQLAlchemyDealStorageRepository


def test_rc174_integrity_audit_detects_tamper():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    DealStorageBase.metadata.create_all(engine)
    session = Session(engine)
    repo = SQLAlchemyDealStorageRepository(session)

    repo.upsert_record(
        deal_id="deal-1",
        payload={"status":"VALIDATED"},
    )
    session.commit()

    record = session.query(
        DealStorageRecord
    ).filter_by(deal_id="deal-1").one()
    record.payload_hash = "tampered"
    session.commit()

    report = repo.audit_integrity()
    assert report["healthy"] is False
    assert report["issue_count"] == 1
