$ErrorActionPreference = "Stop"

Write-Host "=== RC9.1 Decision Context Builder Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc91_decision_context_builder.py tests/test_rc91_decision_context_service.py tests/test_rc91_decision_context_api_contract.py tests/test_rc91_decision_context_api_openapi.py -q

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
Select-String "/api/v1/decision-context/build"

Write-Host ""
Write-Host "=== Decision Context API call ==="

$payload = @{
    product_id = "product-1"
    offer_id = "offer-1"
    deal_score = 95
    authenticity_score = 96
    recommendation = "BUY_NOW"
    recommendation_confidence = 94
    final_decision = "BUY_NOW"
    risk_level = "LOW"
    opportunity_level = "HIGH"
    reason_codes = @("HIGH_DEAL_SCORE")
    explanation = @("Deal score is high.")
} | ConvertTo-Json -Depth 10

Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:8000/api/v1/decision-context/build" `
    -ContentType "application/json" `
    -Body $payload |
ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== RC9.1 Decision Context Builder Validation Passed ==="
