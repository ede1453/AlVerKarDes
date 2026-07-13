
from app.domains.notifications.outbox.outbox_service import NotificationOutboxService


def test_rc79_batch_delivery_summary_exists():
    service = NotificationOutboxService()
    result = service.batch_delivery_summary(["a","b","c"])
    assert result["batch_size"] == 3

def test_rc79_batch_delivery_marks_all_processed():
    service = NotificationOutboxService()
    result = service.batch_delivery_summary(["1","2"])
    assert result["processed_count"] == 2
