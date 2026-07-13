$ErrorActionPreference = "Stop"

Write-Host "=== RC15 LLM Provider Gateway Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc15_llm_provider_registry.py tests/test_rc15_llm_safety_guard.py tests/test_rc15_llm_provider_gateway_engine.py tests/test_rc15_llm_provider_gateway_service.py tests/test_rc15_llm_provider_gateway_api_contract.py tests/test_rc15_llm_provider_gateway_openapi.py tests/test_rc15_llm_gateway_vertical_slice.py -q

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
if (-not $openapi.paths.PSObject.Properties.Name.Contains("/api/v1/llm-gateway/generate")) {
    throw "LLM Provider Gateway endpoint not found in OpenAPI."
}
Write-Host "LLM Provider Gateway endpoint registered."

Write-Host ""
Write-Host "=== LLM Provider Gateway API call ==="

$payload = @{
    provider = "mock"
    model = "mock-shopping-explainer"
    system_prompt = "Explain safely."
    user_prompt = "Explain BUY_NOW."
    guardrails = @("Do not change assistant_decision.")
    structured_context = @{
        assistant_decision = "BUY_NOW"
        confidence = 94
        assistant_context = @{
            product_name = "MacBook Air"
        }
    }
} | ConvertTo-Json -Depth 12

Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:8000/api/v1/llm-gateway/generate" `
    -ContentType "application/json" `
    -Body $payload |
ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== RC15 LLM Provider Gateway Validation Passed ==="
