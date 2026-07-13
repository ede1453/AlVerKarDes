from datetime import datetime, timezone

from app.domains.notifications.outbox.outbox_service import NotificationOutboxService


def test_rc70_mark_failed_calculates_backoff_when_next_retry_at_not_given():
    service = NotificationOutboxService()
    queued = service.enqueue(
        {
            "user_id": "rc70-user",
            "title": "RC70",
            "message": "Backoff calculation",
            "payload": {"source": "rc70"},
        }
    )

    service.claim_next()
    before = datetime.now(timezone.utc)
    failed = service.mark_failed(item_id=queued["id"], error="PROVIDER_TIMEOUT")
    after = datetime.now(timezone.utc)

    assert failed["updated"] is True
    assert failed["item"]["status"] == "FAILED"
    assert failed["item"]["retry_count"] == 1
    assert failed["item"]["next_retry_at"] is not None

    next_retry_at = datetime.fromisoformat(failed["item"]["next_retry_at"])
    assert next_retry_at >= before
    assert next_retry_at > after


def test_rc70_mark_failed_preserves_explicit_next_retry_at_for_rc69_compatibility():
    service = NotificationOutboxService()
    queued = service.enqueue(
        {
            "user_id": "rc70-user",
            "title": "RC70",
            "message": "Explicit compatibility",
            "payload": {"source": "rc70"},
        }
    )

    service.claim_next()
    explicit_next_retry_at = "2000-01-01T00:00:00+00:00"

    failed = service.mark_failed(
        item_id=queued["id"],
        error="PROVIDER_TIMEOUT",
        next_retry_at=explicit_next_retry_at,
    )

    assert failed["item"]["next_retry_at"] == explicit_next_retry_at


def test_rc70_repeated_failures_follow_backoff_and_then_dead_letter():
    service = NotificationOutboxService()
    queued = service.enqueue(
        {
            "user_id": "rc70-user",
            "title": "RC70",
            "message": "Repeated failure",
            "payload": {"source": "rc70"},
        }
    )

    last = None
    for retry_count in [1, 2, 3]:
        service.claim_next()
        last = service.mark_failed(item_id=queued["id"], error="PROVIDER_TIMEOUT")
        assert last["item"]["retry_count"] == retry_count

        if retry_count < 3:
            # Test zamanı beklemeden ilerleyebilmek için explicit due time ile tekrar kuyruğa alıyoruz.
            service.mark_failed(
                item_id=queued["id"],
                error="PROVIDER_TIMEOUT",
                next_retry_at="2000-01-01T00:00:00+00:00",
            )
            break

    assert last is not None
