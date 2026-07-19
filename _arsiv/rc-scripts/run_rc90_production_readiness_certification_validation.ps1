$ErrorActionPreference = "Stop"

Write-Host "=== RC90 Production Readiness Certification Validation ==="

python -m pytest tests/test_rc90_production_readiness_service.py tests/test_rc90_production_readiness_api.py tests/test_rc90_production_readiness_openapi.py tests/test_rc90_production_readiness_vertical_slice.py -q
python -m py_compile app/domains/notifications/outbox/outbox_service.py
python scripts/check_docker_db_env_consistency.py
python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py
python scripts/api_contract_schema_guard.py
python -m pytest -q

Write-Host "=== RC90 Production Readiness Certification Validation Passed ==="
