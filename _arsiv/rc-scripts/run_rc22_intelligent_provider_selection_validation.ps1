$ErrorActionPreference = "Stop"

Write-Host "=== RC22 Intelligent Provider Selection Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc22_provider_selection_engine.py tests/test_rc22_provider_selection_service.py tests/test_rc22_provider_selection_api_contract.py tests/test_rc22_provider_selection_openapi.py tests/test_rc22_intelligent_orchestration_service.py tests/test_rc22_intelligent_orchestration_api_contract.py tests/test_rc22_intelligent_provider_selection_vertical_slice.py -q

Write-Host ""
Write-Host "=== Related health/orchestration tests ==="
python -m pytest tests/test_rc21_provider_health_api_contract.py tests/test_rc19_llm_orchestration_api_contract.py tests/test_rc20_orchestration_audit_api_contract.py -q

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
Write-Host "=== Intelligent orchestration API call ==="

$payload = @{
    candidate_providers = @("mock", "openai", "local")
    model = "mock-shopping-explainer"
    system_prompt = "Explain safely."
    user_prompt = "Explain BUY_NOW."
    guardrails = @("Do not change assistant_decision.")
    structured_context = @{
        assistant_decision = "BUY_NOW"
        assistant_context = @{
            product_name = "MacBook Air"
        }
        prompt_version = "shopping_v1"
    }
    prompt_version = "shopping_v1"
} | ConvertTo-Json -Depth 12

Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:8000/api/v1/llm-orchestration/run-intelligent" `
    -ContentType "application/json" `
    -Body $payload |
ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== RC22 Intelligent Provider Selection Validation Passed ==="
