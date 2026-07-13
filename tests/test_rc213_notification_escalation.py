from app.domains.deal_notifications.operations import DealNotificationOperationsService


def test_rc213_escalation_after_failures():
    service = DealNotificationOperationsService()

    for _ in range(2):
        service.record_delivery_attempt(
            notification_id="n1",
            channel="push",
            provider="provider-a",
            successful=False,
            error="TIMEOUT",
        )

    result = service.create_escalation(
        notification_id="n1",
        current_channel="push",
        fallback_channels=["email","in_app"],
        trigger_after_failures=2,
    )

    assert result["created"] is True
    assert result["escalation"]["status"] == "PENDING"

    completed = service.complete_escalation(
        escalation_id=result[
            "escalation"
        ]["escalation_id"],
        delivered_channel="email",
    )

    assert completed["updated"] is True
    assert completed["escalation"]["status"] == "COMPLETED"
