from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.domains.deal_storage.sqlalchemy_models import DealStorageBase
from app.domains.deal_storage.sqlalchemy_repository import SQLAlchemyDealStorageRepository


def test_rc172_atomic_record_and_outbox():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    DealStorageBase.metadata.create_all(engine)
    repo = SQLAlchemyDealStorageRepository(Session(engine))

    result = repo.save_with_outbox(
        deal_id="deal-1",
        payload={"status":"RECOMMENDED"},
        expected_version=None,
        event_type="DEAL_RECOMMENDED",
        event_payload={"decision":"BUY"},
    )

    assert result["committed"] is True
    events = repo.claim_pending_events()
    assert len(events) == 1
    assert events[0]["status"] == "PROCESSING"

    published = repo.mark_event_published(
        events[0]["id"]
    )
    assert published["status"] == "PUBLISHED"
