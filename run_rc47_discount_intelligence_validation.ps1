$ErrorActionPreference = "Stop"

Write-Host "=== RC47 Discount Intelligence Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc47_discount_intelligence_engine.py tests/test_rc47_discount_intelligence_service.py tests/test_rc47_discount_intelligence_api_contract.py tests/test_rc47_discount_intelligence_openapi.py tests/test_rc47_discount_intelligence_vertical_slice.py -q

Write-Host ""
Write-Host "=== Related intelligence tests ==="
python -m pytest tests/test_rc43_deal_detection_api_contract.py tests/test_rc44_price_prediction_api_contract.py tests/test_rc45_smart_alert_api_contract.py -q

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
Write-Host "=== Discount intelligence API call ==="

$payload = @{
    product_key = "macbook-air"
    current_price = "949.00"
    claimed_original_price = "1099.00"
    price_history = @{
        min_price = "949.00"
        average_price = "999.00"
        max_price = "1099.00"
        trend = "DOWN"
    }
    deal_detection = @{
        deal_score = 95
    }
    price_prediction = @{
        recommendation_hint = "BUY_SOON"
    }
} | ConvertTo-Json -Depth 12

Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/discount-intelligence/analyze" -ContentType "application/json" -Body $payload | ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== RC47 Discount Intelligence Validation Passed ==="
