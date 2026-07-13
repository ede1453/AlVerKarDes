$ErrorActionPreference = "Stop"

Write-Host "=== RC40 Price History Foundation Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc40_price_history_engine.py tests/test_rc40_price_history_service.py tests/test_rc40_price_history_api_contract.py tests/test_rc40_price_history_openapi.py tests/test_rc40_price_history_vertical_slice.py -q

Write-Host ""
Write-Host "=== Related product matching/search tests ==="
python -m pytest tests/test_rc39_product_matching_api_contract.py tests/test_rc38_unified_search_api_contract.py tests/test_rc353_event_test_order_independence.py -q

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
Write-Host "=== Price history API call ==="

Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/price-history/clear" | Out-Null

$payload = @{
    points = @(
        @{ product_key = "macbook-air-m3-13"; marketplace = "amazon"; price = "999.00"; currency = "EUR" },
        @{ product_key = "macbook-air-m3-13"; marketplace = "saturn"; price = "949.00"; currency = "EUR" }
    )
} | ConvertTo-Json -Depth 12

Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/price-history/points/bulk" -ContentType "application/json" -Body $payload | ConvertTo-Json -Depth 12
Invoke-RestMethod -Method Get -Uri "http://localhost:8000/api/v1/price-history/macbook-air-m3-13/summary" | ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== RC40 Price History Foundation Validation Passed ==="
