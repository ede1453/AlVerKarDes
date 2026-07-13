
from app.domains.notifications.outbox.outbox_service import NotificationOutboxService


def test_rc78_priority_queue_defaults_to_normal():
    service = NotificationOutboxService()
    result = service.get_priority_queue("NORMAL")
    assert result["priority"] == "NORMAL"

def test_rc78_priority_queue_orders_urgent_first():
    service = NotificationOutboxService()
    order = service.priority_order(["LOW","URGENT","NORMAL"])
    assert order[0] == "URGENT"
