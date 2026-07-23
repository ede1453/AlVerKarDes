from app.domains.notifications.outbox.outbox_service import NotificationOutboxService


async def test_rc80_digest_summary_empty():
    service = NotificationOutboxService()

    result = await service.build_digest_summary(user_id="rc80-user")

    assert result["user_id"] == "rc80-user"
    assert result["item_count"] == 0
    assert result["items"] == []
    assert result["metadata"]["digest_version"] == "notification_digest_v1"


async def test_rc80_digest_summary_groups_pending_items_for_user():
    service = NotificationOutboxService()

    first = await service.enqueue(
        {
            "user_id": "rc80-user",
            "title": "Deal 1",
            "message": "First deal",
            "payload": {"product_key": "macbook-air"},
        }
    )
    second = await service.enqueue(
        {
            "user_id": "rc80-user",
            "title": "Deal 2",
            "message": "Second deal",
            "payload": {"product_key": "ipad-air"},
        }
    )
    await service.enqueue(
        {
            "user_id": "other-user",
            "title": "Other",
            "message": "Other user deal",
            "payload": {"product_key": "other"},
        }
    )

    result = await service.build_digest_summary(user_id="rc80-user")

    assert result["item_count"] == 2
    assert [item["id"] for item in result["items"]] == [first["id"], second["id"]]
    assert result["summary_title"] == "2 notifications ready"
