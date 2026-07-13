from app.domains.deal_notifications.operations import DealNotificationOperationsService


def test_rc214_digest_sorted_and_limited():
    service = DealNotificationOperationsService()

    result = service.build_digest(
        user_id="u1",
        notifications=[
            {
                "notification_id":"n1",
                "confidence":80,
                "discount_pct":20,
            },
            {
                "notification_id":"n2",
                "confidence":95,
                "discount_pct":30,
            },
        ],
        period_start="2026-07-12T00:00:00+00:00",
        period_end="2026-07-12T23:59:59+00:00",
        maximum_items=1,
    )

    assert result["digest"]["item_count"] == 1
    assert result["digest"]["items"][0]["notification_id"] == "n2"
