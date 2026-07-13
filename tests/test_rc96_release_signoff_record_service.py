from app.domains.notifications.outbox.outbox_service import NotificationOutboxService


def test_rc96_placeholder():
    service = NotificationOutboxService()
    assert service is not None
