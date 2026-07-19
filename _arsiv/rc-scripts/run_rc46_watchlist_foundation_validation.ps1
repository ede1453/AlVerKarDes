$ErrorActionPreference = "Stop"

Write-Host "=== RC46 Watchlist Foundation Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc46_watchlist_repository.py tests/test_rc46_watchlist_service.py tests/test_rc46_watchlist_api_contract.py tests/test_rc46_watchlist_openapi.py tests/test_rc46_watchlist_vertical_slice.py -q

Write-Host ""
Write-Host "=== Related alert/deal/prediction tests ==="
python -m pytest tests/test_rc45_smart_alert_api_contract.py tests/test_rc43_deal_detection_api_contract.py tests/test_rc44_price_prediction_api_contract.py -q

Write-Host ""
Write-Host "=== OpenAPI uniqueness guard ==="
python scripts/check_openapi_uniqueness.py

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
Write-Host "=== Watchlist API call ==="

Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/watchlist/clear" | Out-Null

$itemPayload = @{
    user_id = "validation-user"
    product_key = "macbook-air"
    query = "MacBook Air"
    target_price = "950.00"
    channels = @("in_app")
} | ConvertTo-Json -Depth 12

$item = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/watchlist/items" -ContentType "application/json" -Body $itemPayload
$item | ConvertTo-Json -Depth 12

$evalPayload = @{
    deal_detection = @{
        deal_level = "EXCELLENT_DEAL"
        deal_score = 95
    }
    price_prediction = @{
        recommendation_hint = "BUY_SOON"
    }
    personalization = @{
        top_offer = @{
            personalization_score = 95
        }
    }
    price_history = @{
        latest_price = "949.00"
    }
} | ConvertTo-Json -Depth 12

Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/watchlist/items/$($item.id)/evaluate" -ContentType "application/json" -Body $evalPayload | ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== RC46 Watchlist Foundation Validation Passed ==="
