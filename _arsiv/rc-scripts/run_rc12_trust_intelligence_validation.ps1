$ErrorActionPreference = "Stop"

Write-Host "=== RC12 Trust Intelligence Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc12_trust_engine.py tests/test_rc12_trust_repository.py tests/test_rc12_trust_service.py tests/test_rc12_trust_serializer.py tests/test_rc12_trust_api_contract.py tests/test_rc12_trust_openapi.py tests/test_rc12_trust_vertical_slice.py -q

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
Write-Host "=== OpenAPI registration check ==="
Invoke-RestMethod "http://localhost:8000/openapi.json" |
ConvertTo-Json -Depth 8 |
Select-String "/api/v1/trust-intelligence/evaluate"

Write-Host ""
Write-Host "=== Trust Intelligence API signal ==="

$signalPayload = @{
    source_type = "store"
    source_id = "store-1"
    positive_count = 10
    negative_count = 0
    total_count = 10
} | ConvertTo-Json -Depth 10

Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:8000/api/v1/trust-intelligence/signals" `
    -ContentType "application/json" `
    -Body $signalPayload |
ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== Trust Intelligence API evaluation ==="

$evaluationPayload = @{
    decision_id = "decision-1"
    store_id = "store-1"
    base_confidence = 90
    final_decision = "BUY_NOW"
} | ConvertTo-Json -Depth 10

Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:8000/api/v1/trust-intelligence/evaluate" `
    -ContentType "application/json" `
    -Body $evaluationPayload |
ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== RC12 Trust Intelligence Validation Passed ==="
