
from app.domains.notifications.outbox.outbox_service import NotificationOutboxService


def test_rc77_tenant_quota_default_allows():
    service = NotificationOutboxService()
    result = service.check_tenant_quota("tenant-a")
    assert result["allowed"] is True

def test_rc77_tenant_quota_blocks_after_limit():
    service = NotificationOutboxService()
    for _ in range(3):
        service.register_tenant_delivery("tenant-a")
    result = service.check_tenant_quota("tenant-a", limit=3)
    assert result["allowed"] is False
