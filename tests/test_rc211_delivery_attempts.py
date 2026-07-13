from app.domains.deal_notifications.operations import DealNotificationOperationsService


def test_rc211_delivery_attempt_history():
    service = DealNotificationOperationsService()

    service.record_delivery_attempt(
        notification_id="n1",
        channel="push",
        provider="provider-a",
        successful=False,
        error="TIMEOUT",
        latency_ms=500,
    )

    service.record_delivery_attempt(
        notification_id="n1",
        channel="push",
        provider="provider-a",
        successful=True,
        latency_ms=120,
    )

    result = service.get_delivery_attempts(
        notification_id="n1"
    )

    assert result["attempt_count"] == 2
    assert result["successful_count"] == 1
    assert result["failed_count"] == 1
