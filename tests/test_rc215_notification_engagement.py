from app.domains.deal_notifications.operations import DealNotificationOperationsService


def test_rc215_engagement_metrics():
    service = DealNotificationOperationsService()

    for event_type in [
        "DELIVERED",
        "OPENED",
        "CLICKED",
        "CONVERTED",
    ]:
        service.record_engagement(
            notification_id="n1",
            user_id="u1",
            event_type=event_type,
            channel="push",
        )

    result = service.calculate_engagement_metrics(
        user_id="u1",
        channel="push",
    )

    assert result["counts"]["DELIVERED"] == 1
    assert result["open_rate"] == 1.0
    assert result["click_rate"] == 1.0
    assert result["conversion_rate"] == 1.0
