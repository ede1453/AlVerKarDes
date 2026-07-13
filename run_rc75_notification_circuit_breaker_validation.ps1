$ErrorActionPreference = "Stop"

Write-Host "=== RC75 Notification Circuit Breaker Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc75_notification_circuit_breaker_service.py tests/test_rc75_notification_circuit_breaker_api.py tests/test_rc75_notification_circuit_breaker_openapi.py tests/test_rc75_notification_circuit_breaker_vertical_slice.py -q

Write-Host ""
Write-Host "=== Related tests ==="
python -m pytest tests/test_rc74_notification_channel_health_service.py tests/test_rc73_notification_metrics_service.py tests/test_rc72_dlq_replay_audit_service.py tests/test_rc71_dead_letter_queue_service.py -q

Write-Host ""
Write-Host "=== Guards ==="
python scripts/check_docker_db_env_consistency.py
python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py
python scripts/api_contract_schema_guard.py

Write-Host ""
Write-Host "=== Full test suite ==="
python -m pytest -q

Write-Host ""
Write-Host "=== Docker rebuild ==="
docker compose -f docker-compose.prod.yml down --remove-orphans
docker compose -f docker-compose.prod.yml up -d --build --force-recreate

Write-Host ""
Write-Host "=== Alembic ==="
docker compose -f docker-compose.prod.yml exec -T aici-api alembic upgrade head

Write-Host ""
Write-Host "=== RC75 Notification Circuit Breaker Validation Passed ==="
