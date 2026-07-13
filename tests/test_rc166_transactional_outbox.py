from app.domains.deal_storage.service import DealStorageRepository


def test_rc166_record_and_outbox_commit_together():
    repo = DealStorageRepository()
    result = repo.save_with_outbox(
        deal_id="deal-1",
        payload={"status":"RECOMMENDED"},
        version=1,
        event_type="DEAL_RECOMMENDED",
        event_payload={"decision":"BUY"},
    )
    assert result["committed"] is True
    assert repo.get("deal-1")["payload"]["status"] == "RECOMMENDED"
    events = repo.list_outbox(status="PENDING")
    assert len(events) == 1
    published = repo.mark_outbox_published(
        events[0]["outbox_event_id"]
    )
    assert published["status"] == "PUBLISHED"
