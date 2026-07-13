$ErrorActionPreference = "Stop"

Write-Host "=== RC94 Release Audit Trail Validation ==="

python -m pytest tests/test_rc94_release_audit_trail_service.py tests/test_rc94_release_audit_trail_api.py tests/test_rc94_release_audit_trail_openapi.py tests/test_rc94_release_audit_trail_vertical_slice.py -q
python -m py_compile app/domains/notifications/outbox/outbox_service.py
python scripts/check_docker_db_env_consistency.py
python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py
python scripts/api_contract_schema_guard.py
python -m pytest -q

Write-Host "=== RC94 Release Audit Trail Validation Passed ==="
