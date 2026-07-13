from app.domains.deal_persistence.service import DealPersistenceService


def test_rc163_archive_creates_snapshot():
    service = DealPersistenceService()
    service.persist_deal(
        deal_id="deal-1",
        payload={"status":"EXPIRED"},
    )
    result = service.archive_deal(
        deal_id="deal-1",
        reason="Retention policy",
        actor="system",
    )
    assert result["archived"] is True
    assert result["archive"]["snapshot_id"]
    assert service.get_record(
        "deal-1"
    )["archived"] is True
