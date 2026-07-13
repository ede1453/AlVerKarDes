from app.domains.deal_persistence.service import DealPersistenceService


def test_rc160_persist_and_version_deal():
    service = DealPersistenceService()
    first = service.persist_deal(
        deal_id="deal-1",
        payload={"status":"DISCOVERED","price":899},
    )
    second = service.persist_deal(
        deal_id="deal-1",
        payload={"status":"VALIDATED","price":899},
        expected_version=1,
    )
    assert first["record"]["version"] == 1
    assert second["record"]["version"] == 2

def test_rc160_version_conflict():
    service = DealPersistenceService()
    service.persist_deal(
        deal_id="deal-1",
        payload={"status":"DISCOVERED"},
    )
    result = service.persist_deal(
        deal_id="deal-1",
        payload={"status":"VALIDATED"},
        expected_version=99,
    )
    assert result["persisted"] is False
    assert result["reason"] == "VERSION_CONFLICT"
