$ErrorActionPreference = "Stop"

Write-Host "=== RC19 LLM Orchestration Layer Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc19_provider_routing_policy.py tests/test_rc19_llm_orchestration_engine.py tests/test_rc19_llm_orchestration_service.py tests/test_rc19_llm_orchestration_api_contract.py tests/test_rc19_llm_orchestration_openapi.py tests/test_rc19_llm_orchestration_vertical_slice.py -q

Write-Host ""
Write-Host "=== Related provider/gateway tests ==="
python -m pytest tests/test_rc15_llm_provider_gateway_api_contract.py tests/test_rc16_llm_gateway_external_provider_api_contract.py tests/test_rc18_llm_gateway_plugin_vertical_slice.py -q

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
Write-Host "=== LLM Orchestration API call ==="

$payload = @{
    preferred_provider = "openai"
    fallback_providers = @("mock")
    model = "mock-shopping-explainer"
    system_prompt = "Explain safely."
    user_prompt = "Explain BUY_NOW."
    guardrails = @("Do not change assistant_decision.")
    structured_context = @{
        assistant_decision = "BUY_NOW"
        assistant_context = @{
            product_name = "MacBook Air"
        }
    }
    prompt_version = "shopping_v1"
    max_attempts = 2
} | ConvertTo-Json -Depth 12

Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:8000/api/v1/llm-orchestration/run" `
    -ContentType "application/json" `
    -Body $payload |
ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== RC19 LLM Orchestration Layer Validation Passed ==="
