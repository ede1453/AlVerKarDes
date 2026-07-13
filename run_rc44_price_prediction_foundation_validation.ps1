$ErrorActionPreference = "Stop"

Write-Host "=== RC44 Price Prediction Foundation Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc44_price_prediction_engine.py tests/test_rc44_price_prediction_service.py tests/test_rc44_price_prediction_api_contract.py tests/test_rc44_price_prediction_openapi.py tests/test_rc44_price_prediction_vertical_slice.py -q

Write-Host ""
Write-Host "=== Related price/deal tests ==="
python -m pytest tests/test_rc40_price_history_api_contract.py tests/test_rc43_deal_detection_api_contract.py tests/test_rc42_ai_shopping_agent_api_contract.py -q

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
Write-Host "=== Price prediction API call ==="

$payload = @{
    product_key = "macbook-air"
    price_history = @{
        latest_price = "949.00"
        min_price = "949.00"
        average_price = "999.00"
        max_price = "1099.00"
        trend = "DOWN"
        points = @(
            @{ price = "999.00" },
            @{ price = "949.00" }
        )
    }
    prediction_horizon_days = 7
} | ConvertTo-Json -Depth 12

Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/price-prediction/predict" -ContentType "application/json" -Body $payload | ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== RC44 Price Prediction Foundation Validation Passed ==="
