$ErrorActionPreference = "Stop"

Write-Host "=== RC91 Release Manifest Validation ==="

python -m pytest tests/test_rc91_release_manifest_service.py tests/test_rc91_release_manifest_api.py tests/test_rc91_release_manifest_openapi.py tests/test_rc91_release_manifest_vertical_slice.py -q
python -m py_compile app/domains/notifications/outbox/outbox_service.py
python scripts/check_docker_db_env_consistency.py
python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py
python scripts/api_contract_schema_guard.py
python -m pytest -q

Write-Host "=== RC91 Release Manifest Validation Passed ==="
