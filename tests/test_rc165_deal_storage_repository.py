from app.domains.deal_storage.service import DealStorageRepository


def test_rc165_upsert_and_read_record():
    repo = DealStorageRepository()
    saved = repo.upsert(
        deal_id="deal-1",
        payload={"status":"VALIDATED"},
        version=1,
    )
    assert saved["deal_id"] == "deal-1"
    assert repo.get("deal-1")["version"] == 1
    assert len(saved["payload_hash"]) == 64
