$ErrorActionPreference = "Stop"

Write-Host "=== RC100-RC104 Observability Layer Validation ==="

Write-Host ""
Write-Host "=== Observability grouped tests ==="
python -m pytest `
tests/test_rc100_distributed_tracing.py `
tests/test_rc101_structured_logging.py `
tests/test_rc102_correlation_id.py `
tests/test_rc103_request_timeline.py `
tests/test_rc104_audit_event_stream.py `
tests/test_rc100_rc104_observability_openapi.py -q

Write-Host ""
Write-Host "=== Python compile ==="
python -m py_compile app/core/observability.py
python -m py_compile app/api/v1/observability_router.py
python -m py_compile app/main.py

Write-Host ""
Write-Host "=== Existing guards ==="
python scripts/check_docker_db_env_consistency.py
python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py
python scripts/api_contract_schema_guard.py

Write-Host ""
Write-Host "=== Full regression suite ==="
python -m pytest -q

Write-Host ""
Write-Host "=== RC100-RC104 Observability Layer Validation Passed ==="
