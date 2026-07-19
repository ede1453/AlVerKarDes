$ErrorActionPreference = "Stop"

Write-Host "=== RC58.2 RC58 Test Expectation Update Validation ==="

Write-Host ""
Write-Host "=== Updated expectation tests ==="
python -m pytest tests/test_rc582_recommendation_router_cleanup_expectation.py tests/test_rc58_router_alias_cleanup.py tests/test_rc581_recommendation_duplicate_route_fix.py -q

Write-Host ""
Write-Host "=== Recommendation compatibility tests ==="
python -m pytest tests/test_rc521_recommendation_backward_compatibility.py tests/test_rc522_recommendation_operation_id_compatibility.py -q

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
Write-Host "=== RC58.2 RC58 Test Expectation Update Validation Passed ==="
