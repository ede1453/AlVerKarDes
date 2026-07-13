$ErrorActionPreference = "Stop"

Write-Host "=== RC14 LLM Explanation Adapter Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc14_llm_explanation_prompt_builder.py tests/test_rc14_llm_explanation_engine.py tests/test_rc14_llm_explanation_service.py tests/test_rc14_llm_explanation_api_contract.py tests/test_rc14_llm_explanation_openapi.py tests/test_rc14_llm_explanation_vertical_slice.py -q

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
if (-not $openapi.paths.PSObject.Properties.Name.Contains("/api/v1/llm-explanations/prepare")) {
    throw "LLM Explanation Adapter endpoint not found in OpenAPI."
}
Write-Host "LLM Explanation Adapter endpoint registered."

Write-Host ""
Write-Host "=== LLM Explanation Adapter API call ==="

$payload = @{
    assistant_decision = "BUY_NOW"
    headline = "Buy MacBook Air now"
    summary = "The combined decision supports buying now."
    confidence = 94
    risk_level = "LOW"
    opportunity_level = "HIGH"
    next_actions = @("Check final seller terms before purchase.")
    reason_codes = @("ASSISTANT_BUY_SIGNAL")
    assistant_context = @{
        product_name = "MacBook Air"
    }
    language = "en"
    tone = "clear"
} | ConvertTo-Json -Depth 12

Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:8000/api/v1/llm-explanations/prepare" `
    -ContentType "application/json" `
    -Body $payload |
ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== RC14 LLM Explanation Adapter Validation Passed ==="
