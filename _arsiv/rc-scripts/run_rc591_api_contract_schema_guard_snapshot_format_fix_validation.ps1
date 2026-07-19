$ErrorActionPreference = "Stop"

Write-Host "=== RC59.1 API Contract Schema Guard Snapshot Format Fix Validation ==="

Write-Host ""
Write-Host "=== RC59.1 compatibility tests ==="
python -m pytest tests/test_rc591_schema_guard_snapshot_format_compatibility.py tests/test_rc59_api_contract_schema_guard.py tests/test_rc59_api_contract_schema_guard_script.py -q

Write-Host ""
Write-Host "=== Existing OpenAPI uniqueness guard ==="
python scripts/check_openapi_uniqueness.py

Write-Host ""
Write-Host "=== Existing API contract snapshot guard ==="
python scripts/api_contract_snapshot.py

Write-Host ""
Write-Host "=== API schema contract guard ==="
python scripts/api_contract_schema_guard.py

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
Write-Host "=== RC59.1 API Contract Schema Guard Snapshot Format Fix Validation Passed ==="
