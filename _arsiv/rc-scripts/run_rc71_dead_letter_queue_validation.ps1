$ErrorActionPreference = "Stop"

Write-Host "=== RC71 Dead Letter Queue Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc71_dead_letter_queue_service.py tests/test_rc71_dead_letter_queue_api.py tests/test_rc71_dead_letter_queue_openapi.py tests/test_rc71_dead_letter_queue_vertical_slice.py -q

Write-Host ""
Write-Host "=== Related retry/outbox tests ==="
python -m pytest tests/test_rc70_retry_policy_engine.py tests/test_rc70_retry_policy_service.py tests/test_rc70_retry_policy_api_contract.py tests/test_rc70_retry_policy_vertical_slice.py tests/test_rc69_notification_outbox_retry_scheduler_service.py -q

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
Write-Host "=== DLQ smoke ==="
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/notification-outbox/clear" | ConvertTo-Json -Depth 12

$payload = @{
    user_id = "rc71-docker-user"
    title = "RC71 docker outbox"
    message = "DLQ smoke."
    payload = @{ source = "rc71-docker" }
} | ConvertTo-Json -Depth 10

$queued = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/notification-outbox/enqueue" -ContentType "application/json" -Body $payload

for ($i = 1; $i -le 3; $i++) {
    Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/notification-outbox/claim-next" | Out-Null

    $failedPayload = @{
        error = "PROVIDER_TIMEOUT"
        next_retry_at = "2000-01-01T00:00:00+00:00"
    } | ConvertTo-Json -Depth 10

    $failed = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/notification-outbox/$($queued.id)/mark-failed" -ContentType "application/json" -Body $failedPayload

    if ($failed.item.status -ne "DEAD_LETTER") {
        Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/notification-outbox/requeue-due-retries" | Out-Null
    }
}

Invoke-RestMethod -Method Get -Uri "http://localhost:8000/api/v1/notification-outbox/dead-letters" | ConvertTo-Json -Depth 12
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/notification-outbox/dead-letters/$($queued.id)/replay" | ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== RC71 Dead Letter Queue Validation Passed ==="
