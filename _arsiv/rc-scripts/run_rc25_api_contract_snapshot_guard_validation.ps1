$ErrorActionPreference = "Stop"

Write-Host "=== RC25 API Contract Snapshot Guard Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc25_api_contract_snapshot_extractor.py tests/test_rc25_api_contract_snapshot_compare.py tests/test_rc25_current_api_contract_snapshot.py -q

Write-Host ""
Write-Host "=== API contract snapshot script ==="
python scripts/api_contract_snapshot.py

Write-Host ""
Write-Host "=== Existing OpenAPI uniqueness guard ==="
python scripts/check_openapi_uniqueness.py

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
Write-Host "=== RC25 API Contract Snapshot Guard Validation Passed ==="
