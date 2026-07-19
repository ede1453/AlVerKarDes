$ErrorActionPreference = "Stop"

Write-Host "=== RC16 Real Provider Adapter Boundary Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc16_provider_settings.py tests/test_rc16_external_provider_boundary.py tests/test_rc16_provider_registry.py tests/test_rc16_llm_gateway_external_provider_api_contract.py tests/test_rc16_llm_gateway_openapi.py -q

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
Write-Host "=== Providers endpoint check ==="
Invoke-RestMethod `
    -Method Get `
    -Uri "http://localhost:8000/api/v1/llm-gateway/providers" |
ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== OpenAI boundary call ==="

$payload = @{
    provider = "openai"
    model = "gpt-test"
    system_prompt = "Explain safely."
    user_prompt = "Explain WATCH."
    guardrails = @("Do not change assistant_decision.")
    structured_context = @{
        assistant_decision = "WATCH"
        assistant_context = @{
            product_name = "Phone"
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
Write-Host "=== RC16 Real Provider Adapter Boundary Validation Passed ==="
