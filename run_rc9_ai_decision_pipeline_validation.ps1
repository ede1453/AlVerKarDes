$ErrorActionPreference = "Stop"

Write-Host "=== RC9 AI Decision Pipeline Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc9_ai_decision_pipeline.py tests/test_rc9_ai_decision_pipeline_service.py tests/test_rc9_ai_decision_pipeline_api_contract.py tests/test_rc9_ai_decision_pipeline_api_openapi.py -q

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
Select-String "/api/v1/ai-decision-pipeline/run"

Write-Host ""
Write-Host "=== AI Decision Pipeline API call ==="

$payload = @{
    deal_score = 95
    authenticity_score = 96
    recommendation = "BUY_NOW"
    recommendation_confidence = 94
    trend_direction = "DOWN"
    store_trust_score = 90
    stock_status = "in_stock"
    reason_codes = @("HIGH_DEAL_SCORE", "AUTHENTIC_DISCOUNT")
} | ConvertTo-Json -Depth 10

Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:8000/api/v1/ai-decision-pipeline/run" `
    -ContentType "application/json" `
    -Body $payload |
ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== RC9 AI Decision Pipeline Validation Passed ==="
