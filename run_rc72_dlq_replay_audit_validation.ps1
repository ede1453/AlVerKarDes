$ErrorActionPreference = "Stop"

Write-Host "=== RC72 DLQ Replay Audit Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc72_dlq_replay_audit_service.py tests/test_rc72_dlq_replay_audit_api.py tests/test_rc72_dlq_replay_audit_openapi.py tests/test_rc72_dlq_replay_audit_vertical_slice.py -q

Write-Host ""
Write-Host "=== Related DLQ/retry tests ==="
python -m pytest tests/test_rc71_dead_letter_queue_service.py tests/test_rc71_dead_letter_queue_api.py tests/test_rc70_retry_policy_service.py tests/test_rc69_notification_outbox_retry_scheduler_service.py -q

Write-Host ""
Write-Host "=== Existing guards ==="
python scripts/check_docker_db_env_consistency.py
python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py
python scripts/api_contract_schema_guard.py

Write-Host ""
Write-Host "=== Full test suite ==="
python -m pytest -q

Write-Host ""
Write-Host "=== Docker clean rebuild ==="
docker compose -f docker-compose.prod.yml down --remove-orphans
docker compose -f docker-compose.prod.yml up -d --build --force-recreate

Write-Host ""
Write-Host "=== Alembic upgrade ==="
docker compose -f docker-compose.prod.yml exec -T aici-api alembic upgrade head

Write-Host ""
Write-Host "=== RC72 DLQ Replay Audit Validation Passed ==="
