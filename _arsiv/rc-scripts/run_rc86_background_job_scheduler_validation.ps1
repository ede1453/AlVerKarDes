$ErrorActionPreference = "Stop"

Write-Host "=== RC86 Background Job Scheduler Validation ==="

python -m pytest tests/test_rc86_background_job_scheduler_service.py tests/test_rc86_background_job_scheduler_api.py tests/test_rc86_background_job_scheduler_openapi.py tests/test_rc86_background_job_scheduler_vertical_slice.py -q
python -m py_compile app/domains/notifications/outbox/outbox_service.py
python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py
python scripts/api_contract_schema_guard.py
python -m pytest -q

Write-Host "=== RC86 Background Job Scheduler Validation Passed ==="
