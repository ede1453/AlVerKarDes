$ErrorActionPreference = "Stop"

Write-Host "=== RC13 AI Shopping Assistant Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc13_ai_shopping_assistant_engine.py tests/test_rc13_ai_shopping_assistant_service.py tests/test_rc13_ai_shopping_assistant_serializer.py tests/test_rc13_ai_shopping_assistant_api_contract.py tests/test_rc13_ai_shopping_assistant_openapi.py tests/test_rc13_ai_shopping_assistant_vertical_slice.py -q

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
$openapi = Invoke-RestMethod "http://localhost:8000/openapi.json"
if (-not $openapi.paths.PSObject.Properties.Name.Contains("/api/v1/ai-shopping-assistant/advise")) {
    throw "AI Shopping Assistant endpoint not found in OpenAPI."
}
Write-Host "AI Shopping Assistant endpoint registered."

Write-Host ""
Write-Host "=== AI Shopping Assistant API call ==="

$payload = @{
    user_id = "user-1"
    query = "Should I buy this MacBook?"
    product_name = "MacBook Air"
    product_brand = "apple"
    current_price = "849.00"
    currency = "EUR"
    final_decision = "BUY_NOW"
    confidence = 94
    risk_level = "LOW"
    opportunity_level = "HIGH"
    reason_codes = @("STRONG_BUY_SIGNAL")
    trust_score = 90
    community_score = 88
} | ConvertTo-Json -Depth 10

Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:8000/api/v1/ai-shopping-assistant/advise" `
    -ContentType "application/json" `
    -Body $payload |
ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== RC13 AI Shopping Assistant Validation Passed ==="
