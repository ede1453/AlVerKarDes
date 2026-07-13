$ErrorActionPreference = "Stop"

Write-Host "=== RC12.1 OpenAPI Router Cleanup Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc121_openapi_operation_id_uniqueness.py tests/test_rc12_trust_openapi.py -q

Write-Host ""
Write-Host "=== Router uniqueness script ==="
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
Write-Host "=== OpenAPI duplicate check ==="
$openapi = Invoke-RestMethod "http://localhost:8000/openapi.json"

$operationIds = @()
foreach ($pathName in $openapi.paths.PSObject.Properties.Name) {
    $pathItem = $openapi.paths.$pathName
    foreach ($methodName in $pathItem.PSObject.Properties.Name) {
        if (@("get", "post", "put", "patch", "delete") -contains $methodName.ToLower()) {
            $operationId = $pathItem.$methodName.operationId
            if ($operationId) {
                $operationIds += $operationId
            }
        }
    }
}

$duplicates = $operationIds |
    Group-Object |
    Where-Object { $_.Count -gt 1 }

if ($duplicates.Count -gt 0) {
    $duplicates | Format-Table -AutoSize
    throw "Duplicate OpenAPI operationId values detected."
}

Write-Host "No duplicate OpenAPI operationId values detected."

Write-Host ""
Write-Host "=== RC12.1 OpenAPI Router Cleanup Validation Passed ==="
