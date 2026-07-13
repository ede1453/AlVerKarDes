$ErrorActionPreference = "Stop"

Write-Host "=== RC38 Unified Search Foundation Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc38_unified_search_service.py tests/test_rc38_unified_search_api_contract.py tests/test_rc38_unified_search_openapi.py tests/test_rc38_unified_search_vertical_slice.py -q

Write-Host ""
Write-Host "=== Related marketplace/cache/event tests ==="
python -m pytest tests/test_rc37_marketplace_api_contract.py tests/test_rc33_cache_api_contract.py tests/test_rc35_event_bus_api_contract.py tests/test_rc353_event_test_order_independence.py -q

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
Write-Host "=== Unified search API call ==="

$payload = @{
    query = "MacBook Air"
    user_id = "validation-user"
    marketplaces = @("amazon", "saturn")
    offers = @(
        @{ marketplace = "amazon"; seller = "Amazon"; product_name = "MacBook Air M3"; price = "999.00"; currency = "EUR" },
        @{ marketplace = "saturn"; seller = "Saturn"; product_name = "MacBook Air M3"; price = "949.00"; currency = "EUR" }
    )
} | ConvertTo-Json -Depth 12

Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:8000/api/v1/unified-search/search" `
    -ContentType "application/json" `
    -Body $payload |
ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== RC38 Unified Search Foundation Validation Passed ==="
