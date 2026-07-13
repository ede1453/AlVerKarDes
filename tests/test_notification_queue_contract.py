from app.domains.notifications.models import PendingNotification
from app.domains.notifications.schemas import PendingNotificationCreate, PendingNotificationRead


def test_pending_notification_table_name():
    assert PendingNotification.__tablename__ == "pending_notifications"


def test_pending_notification_create_schema_fields():
    fields = PendingNotificationCreate.model_fields

    assert "user_id" in fields
    assert "offer_id" in fields
    assert "rule_id" in fields
    assert "channel" in fields
    assert "title" in fields
    assert "message" in fields


def test_pending_notification_read_from_attributes_enabled():
    assert PendingNotificationRead.model_config["from_attributes"] is True
