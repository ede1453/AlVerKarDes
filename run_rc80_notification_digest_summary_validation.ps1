$ErrorActionPreference = "Stop"

Write-Host "=== RC80 Notification Digest Summary Validation ==="

python -m pytest tests/test_rc80_notification_digest_summary_service.py tests/test_rc80_notification_digest_summary_api.py tests/test_rc80_notification_digest_summary_openapi.py tests/test_rc80_notification_digest_summary_vertical_slice.py -q
python -m pytest tests/test_rc79_notification_batch_delivery_service.py tests/test_rc78_notification_priority_queue_service.py tests/test_rc77_notification_tenant_quota_service.py -q
python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py
python scripts/api_contract_schema_guard.py
python -m pytest -q

Write-Host "=== RC80 Notification Digest Summary Validation Passed ==="
