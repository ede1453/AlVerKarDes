$ErrorActionPreference = "Stop"

Write-Host "=== RC35.1 Event Repository Singleton Fix Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc351_event_repository_singleton.py tests/test_rc351_event_api_singleton_contract.py tests/test_rc351_provider_scheduler_event_visibility.py tests/test_rc36_provider_scheduler_vertical_slice.py -q

Write-Host ""
Write-Host "=== Related event/scheduler tests ==="
python -m pytest tests/test_rc35_event_bus_api_contract.py tests/test_rc35_event_bus_vertical_slice.py tests/test_rc36_provider_scheduler_api_contract.py -q

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
Write-Host "=== Event singleton visibility check ==="

Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/events/clear" | Out-Null

$eventPayload = @{
    event_type = "validation.singleton"
    source = "validation"
    payload = @{
        ok = $true
    }
} | ConvertTo-Json -Depth 12

$event = Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:8000/api/v1/events/publish" `
    -ContentType "application/json" `
    -Body $eventPayload

$events = Invoke-RestMethod `
    -Method Get `
    -Uri "http://localhost:8000/api/v1/events?event_type=validation.singleton&source=validation"

$found = $false
foreach ($item in $events.items) {
    if ($item.id -eq $event.id) {
        $found = $true
        break
    }
}

if (-not $found) {
    throw "Published event was not visible through event list endpoint."
}

Write-Host "Event singleton visibility verified."

Write-Host ""
Write-Host "=== RC35.1 Event Repository Singleton Fix Validation Passed ==="
