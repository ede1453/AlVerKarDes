from app.domains.deal_storage.resilience import DealStorageResilienceService


def test_rc177_retry_then_dead_letter_and_replay():
    service = DealStorageResilienceService()
    event = service.enqueue_outbox(
        aggregate_id="deal-1",
        event_type="DEAL_UPDATED",
        payload={},
    )["event"]

    service.claim_publish_batch()
    retry = service.mark_publish_failed(
        event_id=event["event_id"],
        error="TIMEOUT",
        max_attempts=2,
        base_delay_seconds=1,
    )
    assert retry["status"] == "RETRY"

    service._outbox_events[
        event["event_id"]
    ]["next_attempt_at"] = "2020-01-01T00:00:00+00:00"

    service.claim_publish_batch()
    dead = service.mark_publish_failed(
        event_id=event["event_id"],
        error="TIMEOUT",
        max_attempts=2,
        base_delay_seconds=1,
    )
    assert dead["status"] == "DEAD_LETTER"

    replay = service.replay_dead_letter(
        dead["dead_letter"]["dead_letter_id"]
    )
    assert replay["replayed"] is True
    assert replay["event"]["status"] == "PENDING"
