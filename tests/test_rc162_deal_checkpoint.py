from app.domains.deal_persistence.service import DealPersistenceService


def test_rc162_checkpoint_tracks_lifecycle():
    service = DealPersistenceService()
    service.persist_deal(
        deal_id="deal-1",
        payload={"status":"RECOMMENDED"},
    )
    result = service.create_checkpoint(
        deal_id="deal-1",
        lifecycle_status="RECOMMENDED",
        decision_version=2,
        event_cursor=7,
    )
    latest = service.latest_checkpoint(
        "deal-1"
    )
    assert result["created"] is True
    assert latest["decision_version"] == 2
    assert latest["event_cursor"] == 7
