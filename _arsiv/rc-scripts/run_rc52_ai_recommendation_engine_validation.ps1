$ErrorActionPreference = "Stop"

Write-Host "=== RC52 AI Recommendation Engine Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc52_recommendation_engine.py tests/test_rc52_recommendation_service.py tests/test_rc52_recommendation_api_contract.py tests/test_rc52_recommendation_openapi.py tests/test_rc52_recommendation_vertical_slice.py -q

Write-Host ""
Write-Host "=== Related canonical/intelligence tests ==="
python -m pytest tests/test_rc51_product_canonicalization_api_contract.py tests/test_rc47_discount_intelligence_api_contract.py tests/test_rc43_deal_detection_api_contract.py -q

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
Write-Host "=== Recommendation API call ==="

$payload = @{
    query = "MacBook Air"
    user_id = "validation-user"
    candidates = @(
        @{ product_key = "macbook-air-amazon"; product_name = "MacBook Air Amazon"; marketplace = "amazon"; price = "999.00" },
        @{ product_key = "macbook-air-saturn"; product_name = "MacBook Air Saturn"; marketplace = "saturn"; price = "949.00"; canonical_confidence = 95 }
    )
    personalization = @{ top_offer = @{ marketplace = "saturn" } }
    deal_detection = @{ deal_level = "EXCELLENT_DEAL" }
    discount_intelligence = @{ discount_quality = "EXCELLENT_REAL_DISCOUNT"; fake_discount_risk = "LOW" }
    price_prediction = @{ recommendation_hint = "BUY_SOON" }
} | ConvertTo-Json -Depth 12

Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/recommendations/recommend" -ContentType "application/json" -Body $payload | ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== RC52 AI Recommendation Engine Validation Passed ==="
