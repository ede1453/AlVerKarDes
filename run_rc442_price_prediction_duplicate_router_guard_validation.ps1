$ErrorActionPreference = "Stop"

Write-Host "=== RC44.2 Price Prediction Duplicate Router Guard Validation ==="

Write-Host ""
Write-Host "=== Targeted duplicate guard tests ==="
python -m pytest tests/test_rc442_price_prediction_no_duplicate_operation_ids.py tests/test_rc441_price_prediction_router_registration.py tests/test_rc44_price_prediction_openapi.py -q

Write-Host ""
Write-Host "=== Existing OpenAPI uniqueness guard ==="
python scripts/check_openapi_uniqueness.py

Write-Host ""
Write-Host "=== RC44 targeted tests ==="
python -m pytest tests/test_rc44_price_prediction_engine.py tests/test_rc44_price_prediction_service.py tests/test_rc44_price_prediction_api_contract.py tests/test_rc44_price_prediction_openapi.py tests/test_rc44_price_prediction_vertical_slice.py -q

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
Write-Host "=== OpenAPI duplicate operationId smoke ==="

$openapi = Invoke-RestMethod -Method Get -Uri "http://localhost:8000/openapi.json"
$operationIds = @()

foreach ($pathName in $openapi.paths.PSObject.Properties.Name) {
    $pathItem = $openapi.paths.$pathName
    foreach ($method in $pathItem.PSObject.Properties.Name) {
        $operation = $pathItem.$method
        if ($operation.operationId) {
            $operationIds += $operation.operationId
        }
    }
}

$duplicates = $operationIds | Group-Object | Where-Object { $_.Count -gt 1 }

if ($duplicates.Count -gt 0) {
    $duplicates | Format-Table -AutoSize
    throw "Duplicate operationId values detected."
}

Write-Host "No duplicate operationId values detected."

Write-Host ""
Write-Host "=== RC44.2 Price Prediction Duplicate Router Guard Validation Passed ==="
