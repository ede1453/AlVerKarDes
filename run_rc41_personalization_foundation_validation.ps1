$ErrorActionPreference = "Stop"

Write-Host "=== RC41 Personalization Foundation Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc41_personalization_engine.py tests/test_rc41_personalization_service.py tests/test_rc41_personalization_api_contract.py tests/test_rc41_personalization_openapi.py tests/test_rc41_personalization_vertical_slice.py -q

Write-Host ""
Write-Host "=== Related search/matching/price tests ==="
python -m pytest tests/test_rc38_unified_search_api_contract.py tests/test_rc39_product_matching_api_contract.py tests/test_rc40_price_history_api_contract.py -q

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
Write-Host "=== Personalization API call ==="

Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/personalization/clear" | Out-Null

$profile = @{
    user_id = "validation-user"
    preferred_marketplaces = @("saturn")
    preferred_brands = @("Apple")
    max_price = "1000.00"
} | ConvertTo-Json -Depth 12

Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/personalization/profiles" -ContentType "application/json" -Body $profile | ConvertTo-Json -Depth 12

$score = @{
    user_id = "validation-user"
    offers = @(
        @{ id = "1"; marketplace = "amazon"; product_name = "Apple MacBook Air"; price = "999.00"; currency = "EUR" },
        @{ id = "2"; marketplace = "saturn"; product_name = "Apple MacBook Air"; price = "949.00"; currency = "EUR" }
    )
} | ConvertTo-Json -Depth 12

Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/personalization/score" -ContentType "application/json" -Body $score | ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== RC41 Personalization Foundation Validation Passed ==="
