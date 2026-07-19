$ErrorActionPreference = "Stop"

Write-Host "=== RC67 Notification Outbox Foundation Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc67_notification_outbox_models.py tests/test_rc67_notification_outbox_repository.py tests/test_rc67_notification_outbox_service.py tests/test_rc67_notification_outbox_migration_contract.py -q

Write-Host ""
Write-Host "=== Related notification tests ==="
python -m pytest tests/test_rc66_notification_idempotency_contract.py tests/test_rc66_notification_retry_shape_contract.py tests/test_rc65_notification_delivery_contract.py tests/test_rc53_notification_service.py -q

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
Write-Host "=== Wait for API readiness ==="
$ready = $false
for ($i = 1; $i -le 30; $i++) {
    try {
        Invoke-RestMethod "http://localhost:8000/health" | Out-Null
        $ready = $true
        break
    }
    catch {
        Write-Host "Waiting for API... attempt $i/30"
        Start-Sleep -Seconds 2
    }
}

if (-not $ready) {
    docker compose -f docker-compose.prod.yml logs --tail=160 aici-api
    throw "API did not become ready."
}

Write-Host ""
Write-Host "=== Notification delivery smoke ==="
$payload = @{
    user_id = "rc67-docker-user"
    channels = @("in_app")
    title = "RC67 notification"
    message = "Outbox foundation compatibility smoke."
    payload = @{ source = "rc67-docker" }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/notifications/deliver" -ContentType "application/json" -Body $payload | ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== RC67 Notification Outbox Foundation Validation Passed ==="
