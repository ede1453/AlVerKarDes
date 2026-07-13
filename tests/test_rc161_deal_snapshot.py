from app.domains.deal_persistence.service import DealPersistenceService


def test_rc161_create_snapshot():
    service = DealPersistenceService()
    service.persist_deal(
        deal_id="deal-1",
        payload={"status":"VALIDATED","price":899},
    )
    result = service.create_snapshot(
        deal_id="deal-1"
    )
    assert result["created"] is True
    assert result["snapshot"]["record_version"] == 1
    assert len(result["snapshot"]["snapshot_hash"]) == 64
