from app.domains.deal_persistence.service import DealPersistenceService


def test_rc164_recover_snapshot():
    service = DealPersistenceService()
    service.persist_deal(
        deal_id="deal-1",
        payload={"status":"VALIDATED","price":899},
    )
    snapshot = service.create_snapshot(
        deal_id="deal-1"
    )["snapshot"]
    service.persist_deal(
        deal_id="deal-1",
        payload={"status":"REJECTED","price":899},
        expected_version=1,
    )
    result = service.recover_from_snapshot(
        snapshot_id=snapshot["snapshot_id"],
        expected_snapshot_hash=snapshot["snapshot_hash"],
    )
    assert result["recovered"] is True
    assert result["record"]["payload"]["status"] == "VALIDATED"
    assert result["record"]["version"] == 3

def test_rc164_hash_mismatch_rejected():
    service = DealPersistenceService()
    service.persist_deal(
        deal_id="deal-1",
        payload={"status":"VALIDATED"},
    )
    snapshot = service.create_snapshot(
        deal_id="deal-1"
    )["snapshot"]
    result = service.recover_from_snapshot(
        snapshot_id=snapshot["snapshot_id"],
        expected_snapshot_hash="invalid",
    )
    assert result["recovered"] is False
    assert result["reason"] == "SNAPSHOT_HASH_MISMATCH"
