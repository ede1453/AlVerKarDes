$ErrorActionPreference = "Stop"

Write-Host "=== RC58.1 Recommendation Duplicate Route Fix Validation ==="

Write-Host ""
Write-Host "=== Duplicate route regression tests ==="
python -m pytest tests/test_rc581_recommendation_duplicate_route_fix.py tests/test_rc121_openapi_operation_id_uniqueness.py -q

Write-Host ""
Write-Host "=== Recommendation backward compatibility tests ==="
python -m pytest tests/test_rc521_recommendation_backward_compatibility.py tests/test_rc522_recommendation_operation_id_compatibility.py -q

Write-Host ""
Write-Host "=== OpenAPI uniqueness guard ==="
python scripts/check_openapi_uniqueness.py

Write-Host ""
Write-Host "=== API contract snapshot guard ==="
python scripts/api_contract_snapshot.py

Write-Host ""
Write-Host "=== RC58 targeted tests ==="
python -m pytest tests/test_rc58_router_alias_cleanup.py tests/test_rc58_release_hygiene_scripts.py -q

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
Write-Host "=== Recommendation compatibility smoke ==="

$payload = @{
    query = "MacBook Air"
    user_id = "validation-user"
    candidates = @(
        @{
            product_key = "macbook-air-saturn"
            product_name = "MacBook Air Saturn"
            marketplace = "saturn"
            price = "949.00"
            canonical_confidence = 95
        }
    )
} | ConvertTo-Json -Depth 12

$result = Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:8000/api/v1/recommendations/analyze" `
    -ContentType "application/json" `
    -Body $payload

$result | ConvertTo-Json -Depth 12

Invoke-RestMethod `
    -Method Get `
    -Uri "http://localhost:8000/api/v1/recommendations/sessions/$($result.run_id)" |
ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== RC58.1 Recommendation Duplicate Route Fix Validation Passed ==="
