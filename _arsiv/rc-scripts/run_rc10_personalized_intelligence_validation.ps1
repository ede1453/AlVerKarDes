$ErrorActionPreference = "Stop"

Write-Host "=== RC10 Personalized Intelligence Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc10_personalized_intelligence_engine.py tests/test_rc10_user_preference_repository.py tests/test_rc10_personalized_intelligence_service.py tests/test_rc10_personalized_intelligence_api_contract.py tests/test_rc10_personalized_intelligence_openapi.py -q

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
Select-String "/api/v1/personalized-intelligence/profiles"

Write-Host ""
Write-Host "=== Personalized Intelligence API call ==="

$profilePayload = @{
    user_id = "user-1"
    preferred_brands = @("apple")
    price_sensitivity = "MEDIUM"
    minimum_confidence = 70
} | ConvertTo-Json -Depth 10

Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:8000/api/v1/personalized-intelligence/profiles" `
    -ContentType "application/json" `
    -Body $profilePayload |
ConvertTo-Json -Depth 12

$decisionPayload = @{
    user_id = "user-1"
    final_decision = "BUY_NOW"
    confidence = 90
    product_brand = "apple"
    opportunity_level = "HIGH"
} | ConvertTo-Json -Depth 10

Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:8000/api/v1/personalized-intelligence/decisions/personalize" `
    -ContentType "application/json" `
    -Body $decisionPayload |
ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== RC10 Personalized Intelligence Validation Passed ==="
