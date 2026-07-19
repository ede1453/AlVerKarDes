$ErrorActionPreference = "Stop"

Write-Host "=== RC58 Release Hygiene + Router Cleanup Validation ==="

Write-Host ""
Write-Host "=== RC58 targeted tests ==="
python -m pytest tests/test_rc58_router_alias_cleanup.py tests/test_rc58_release_hygiene_scripts.py -q

Write-Host ""
Write-Host "=== Existing router/OpenAPI guards ==="
python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py

Write-Host ""
Write-Host "=== RC57 pipeline smoke tests ==="
python -m pytest tests/test_rc57_shopping_pipeline_service.py tests/test_rc57_shopping_pipeline_api_contract.py tests/test_rc57_shopping_pipeline_openapi.py tests/test_rc57_shopping_pipeline_vertical_slice.py -q

Write-Host ""
Write-Host "=== Full test suite ==="
python -m pytest -q

Write-Host ""
Write-Host "=== Build clean release ZIP ==="
python scripts/build_release_zip.py --source . --output dist\aici_backend_clean_rc58.zip
python scripts/check_release_hygiene.py dist\aici_backend_clean_rc58.zip

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
Write-Host "=== RC58 Release Hygiene + Router Cleanup Validation Passed ==="
