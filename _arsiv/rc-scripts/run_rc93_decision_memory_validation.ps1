$ErrorActionPreference = "Stop"

Write-Host "=== RC9.3 Decision Memory Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc93_decision_memory_engine.py tests/test_rc93_learning_engine.py tests/test_rc93_decision_memory_repository.py tests/test_rc93_decision_memory_service.py tests/test_rc93_decision_memory_api_contract.py tests/test_rc93_decision_memory_openapi.py -q

Write-Host ""
Write-Host "=== Full test suite ==="
python -m pytest -q

Write-Host ""
Write-Host "=== Docker rebuild ==="
docker compose -f docker-compose.prod.yml up -d --build --force-recreate

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
Select-String "/api/v1/decision-memory/store"

Write-Host ""
Write-Host "=== Decision Memory API call ==="

$payload = @{
    product_id = "product-1"
    offer_id = "offer-1"
    final_decision = "BUY_NOW"
    confidence = 94
    risk_level = "LOW"
    opportunity_level = "HIGH"
    deal_score = 95
    authenticity_score = 96
    recommendation = "BUY_NOW"
    reason_codes = @("STRONG_BUY_SIGNAL")
    decision_context = @{
        context_id = "ctx-1"
    }
} | ConvertTo-Json -Depth 10

$saved = Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:8000/api/v1/decision-memory/store" `
    -ContentType "application/json" `
    -Body $payload

$saved | ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== Decision Memory Outcome API call ==="

$outcomePayload = @{
    decision_price = "100.00"
    future_price = "120.00"
} | ConvertTo-Json -Depth 10

Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:8000/api/v1/decision-memory/$($saved.id)/outcome" `
    -ContentType "application/json" `
    -Body $outcomePayload |
ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== RC9.3 Decision Memory Validation Passed ==="
