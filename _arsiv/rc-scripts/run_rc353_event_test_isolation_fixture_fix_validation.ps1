$ErrorActionPreference = "Stop"

Write-Host "=== RC35.3 Event Test Isolation Fixture Fix Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc35_event_bus_service.py tests/test_rc352_event_test_isolation.py tests/test_rc353_event_test_order_independence.py tests/test_rc351_event_repository_singleton.py tests/test_rc351_event_api_singleton_contract.py tests/test_rc351_provider_scheduler_event_visibility.py -q

Write-Host ""
Write-Host "=== RC36 scheduler tests ==="
python -m pytest tests/test_rc36_provider_scheduler_repository.py tests/test_rc36_provider_scheduler_service.py tests/test_rc36_provider_scheduler_api_contract.py tests/test_rc36_provider_scheduler_openapi.py tests/test_rc36_provider_scheduler_vertical_slice.py -q

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
Write-Host "=== Event repository clear smoke ==="

Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/events/clear" | Out-Null

$status = Invoke-RestMethod -Method Get -Uri "http://localhost:8000/api/v1/events/status"

if ($status.event_count -ne 0) {
    throw "Event repository was not cleared."
}

Write-Host "Event repository clear verified."

Write-Host ""
Write-Host "=== RC35.3 Event Test Isolation Fixture Fix Validation Passed ==="
