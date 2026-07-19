$ErrorActionPreference = "Stop"

Write-Host "=== RC51 Product Canonicalization v2 Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc51_product_canonicalization_rules.py tests/test_rc51_product_canonicalization_engine.py tests/test_rc51_product_canonicalization_service.py tests/test_rc51_product_canonicalization_api_contract.py tests/test_rc51_product_canonicalization_openapi.py tests/test_rc51_product_canonicalization_vertical_slice.py -q

Write-Host ""
Write-Host "=== Related crawler/matching tests ==="
python -m pytest tests/test_rc50_crawler_api_contract.py tests/test_rc39_product_matching_api_contract.py tests/test_rc49_marketplace_connector_api_contract.py -q

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
Write-Host "=== Product canonicalization API call ==="

$payload = @{
    query = "MacBook Air"
    offers = @(
        @{ id = "1"; marketplace = "amazon"; product_name = "Apple MacBook Air M3 13 inch 512GB"; price = "999.00"; currency = "EUR" },
        @{ id = "2"; marketplace = "saturn"; product_name = "Apple MacBook Air M3 13 inch 512GB"; price = "949.00"; currency = "EUR" }
    )
} | ConvertTo-Json -Depth 12

Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/product-canonicalization/canonicalize" -ContentType "application/json" -Body $payload | ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== RC51 Product Canonicalization v2 Validation Passed ==="
