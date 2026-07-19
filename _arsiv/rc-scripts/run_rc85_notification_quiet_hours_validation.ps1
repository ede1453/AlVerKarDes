$ErrorActionPreference = "Stop"

Write-Host "=== RC85 Notification Quiet Hours Validation ==="

python -m pytest tests/test_rc85_notification_quiet_hours_service.py tests/test_rc85_notification_quiet_hours_api.py tests/test_rc85_notification_quiet_hours_openapi.py tests/test_rc85_notification_quiet_hours_vertical_slice.py -q
python -m py_compile app/domains/notifications/outbox/outbox_service.py
python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py
python scripts/api_contract_schema_guard.py
python -m pytest -q

Write-Host "=== RC85 Notification Quiet Hours Validation Passed ==="
