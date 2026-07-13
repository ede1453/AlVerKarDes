$ErrorActionPreference = "Stop"

Write-Host "=== RC23 Retry Backoff Timeout Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc23_retry_policy.py tests/test_rc23_timeout_classifier.py tests/test_rc23_orchestration_retry_metadata.py tests/test_rc23_orchestration_api_contract.py tests/test_rc23_orchestration_openapi.py tests/test_rc23_retry_backoff_vertical_slice.py -q

Write-Host ""
Write-Host "=== Related orchestration tests ==="
python -m pytest tests/test_rc19_llm_orchestration_api_contract.py tests/test_rc22_intelligent_orchestration_api_contract.py tests/test_rc20_orchestration_audit_api_contract.py -q

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
Write-Host "=== Retry backoff orchestration API call ==="

$payload = @{
    preferred_provider = "openai"
    fallback_providers = @("mock")
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
    max_attempts = 2
    timeout_ms = 1000
} | ConvertTo-Json -Depth 12

Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:8000/api/v1/llm-orchestration/run" `
    -ContentType "application/json" `
    -Body $payload |
ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== RC23 Retry Backoff Timeout Validation Passed ==="
