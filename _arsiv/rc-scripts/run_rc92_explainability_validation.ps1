$ErrorActionPreference = "Stop"

Write-Host "=== RC9.2 Explainability Engine Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc92_explainability_engine.py tests/test_rc92_explanation_service.py tests/test_rc92_explanation_reason_tree.py tests/test_rc92_explanation_confidence_breakdown.py tests/test_rc92_explanation_api_contract.py tests/test_rc92_explanation_api_openapi.py -q

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
Select-String "/api/v1/explanations/generate"

Write-Host ""
Write-Host "=== Explanation API call ==="

$payload = @{
    final_decision = "BUY_NOW"
    confidence = 94
    risk_level = "LOW"
    opportunity_level = "HIGH"
    reason_codes = @("STRONG_BUY_SIGNAL")
    scores = @{
        deal_score = 95
        authenticity_score = 96
    }
    market = @{
        country = "DE"
        currency = "EUR"
    }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:8000/api/v1/explanations/generate" `
    -ContentType "application/json" `
    -Body $payload |
ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== RC9.2 Explainability Engine Validation Passed ==="
