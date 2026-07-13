
from app.domains.notifications.outbox.outbox_service import NotificationOutboxService


def test_rc76_rate_limiter_default_allows_requests():
    service = NotificationOutboxService()
    result = service.check_rate_limit("user1")
    assert result["allowed"] is True
    assert result["remaining"] >= 0

def test_rc76_rate_limiter_blocks_after_threshold():
    service = NotificationOutboxService()
    for _ in range(5):
        service.register_delivery_attempt("user1")
    result = service.check_rate_limit("user1", limit=5)
    assert result["allowed"] is False
