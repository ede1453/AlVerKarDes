python -m pytest tests/test_rc84_notification_muting_service.py tests/test_rc84_notification_muting_api.py tests/test_rc84_notification_muting_openapi.py -q
python -m py_compile app/domains/notifications/outbox/outbox_service.py
python -m pytest -q
