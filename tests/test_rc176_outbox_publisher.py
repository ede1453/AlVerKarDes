from app.domains.deal_storage.resilience import DealStorageResilienceService


def test_rc176_claim_and_publish():
    service = DealStorageResilienceService()
    event = service.enqueue_outbox(
        aggregate_id="deal-1",
        event_type="DEAL_UPDATED",
        payload={"status":"VALIDATED"},
    )["event"]

    claimed = service.claim_publish_batch()
    assert claimed["claimed_count"] == 1
    assert claimed["events"][0]["status"] == "PROCESSING"

    published = service.mark_published(
        event["event_id"]
    )
    assert published["event"]["status"] == "PUBLISHED"
