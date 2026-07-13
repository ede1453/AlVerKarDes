from app.domains.deal_storage.service import DealStorageRepository


def test_rc168_integrity_audit_healthy():
    repo = DealStorageRepository()
    repo.upsert(
        deal_id="deal-1",
        payload={"status":"VALIDATED"},
        version=1,
    )
    report = repo.audit_integrity()
    assert report["healthy"] is True
    assert report["issue_count"] == 0

def test_rc168_integrity_audit_detects_tampering():
    repo = DealStorageRepository()
    repo.upsert(
        deal_id="deal-1",
        payload={"status":"VALIDATED"},
        version=1,
    )
    repo._records["deal-1"]["payload"]["status"] = "TAMPERED"
    report = repo.audit_integrity()
    assert report["healthy"] is False
    assert report["issues"][0]["issue"] == "PAYLOAD_HASH_MISMATCH"
