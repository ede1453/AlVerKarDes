$ErrorActionPreference = "Stop"

Write-Host "=== RC35 Event Bus Layer Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc35_event_repository.py tests/test_rc35_event_bus_service.py tests/test_rc35_event_bus_api_contract.py tests/test_rc35_event_bus_openapi.py tests/test_rc35_event_bus_vertical_slice.py -q

Write-Host ""
Write-Host "=== Related job/cache tests ==="
python -m pytest tests/test_rc34_job_queue_api_contract.py tests/test_rc33_cache_api_contract.py -q

Write-Host ""
Write-Host "=== API contract snapshot guard ==="
python scripts/api_contract_snapshot.py

Write-Host ""
Write-Host "=== Full test suite ==="
python -m pytest -q

Write-Host ""
Write-Host "=== Docker rebuild ==="
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
Write-Host "=== Event publish API call ==="

$payload = @{
    event_type = "validation.completed"
    source = "validation"
    payload = @{
        status = "ok"
    }
    metadata = @{
        event_version = "event_v1"
    }
} | ConvertTo-Json -Depth 12

Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:8000/api/v1/events/publish" `
    -ContentType "application/json" `
    -Body $payload |
ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== Event status API call ==="
Invoke-RestMethod `
    -Method Get `
    -Uri "http://localhost:8000/api/v1/events/status" |
ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== RC35 Event Bus Layer Validation Passed ==="
