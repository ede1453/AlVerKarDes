from app.domains.deal_notifications.service import DealNotificationService


def test_rc210_build_and_deliver_notification():
    service = DealNotificationService()
    service.preferences.set_preferences(
        user_id="user-1",
        enabled_channels=["push","in_app"],
        minimum_confidence=70,
        minimum_discount_pct=20,
        quiet_hours_enabled=False,
    )

    created = service.build_notification(
        user_id="user-1",
        at_time="2026-07-12T12:00:00+03:00",
        deal={
            "deal_id":"deal-1",
            "canonical_product_key":"product-1",
            "decision":"BUY",
            "confidence_score":85,
            "observed_discount_pct":25,
            "freshness_status":"FRESH",
            "anomaly_detected":False,
            "effective_price":700,
            "source_id":"amazon",
        },
    )

    assert created["created"] is True
    assert created["notification"]["status"] == "READY"

    delivered = service.mark_delivered(
        notification_id=created[
            "notification"
        ]["notification_id"],
        channel="push",
    )

    assert delivered["updated"] is True
    assert delivered["notification"]["status"] == "DELIVERED"
