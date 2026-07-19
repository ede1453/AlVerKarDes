$ErrorActionPreference = "Stop"

Write-Host "=== RC29 Orchestration DB Audit Persistence Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc29_orchestration_db_audit_openapi.py tests/test_rc29_orchestration_db_audit_dependency_override.py tests/test_rc29_orchestration_db_audit_backward_compatibility.py -q

Write-Host ""
Write-Host "=== Related DB audit tests ==="
python -m pytest tests/test_rc28_llm_audit_db_readback_contract.py tests/test_rc27_llm_audit_db_router_contract.py tests/test_rc26_llm_audit_sql_repository.py -q

Write-Host ""
Write-Host "=== API contract snapshot guard ==="
python scripts/api_contract_snapshot.py

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
Write-Host "=== Orchestration DB audit create/readback verification ==="

$openapi = Invoke-RestMethod "http://localhost:8000/openapi.json"
$hasDbEndpoint = $openapi.paths.PSObject.Properties.Name.Contains("/api/v1/llm-orchestration/run-with-db-audit")

if (-not $hasDbEndpoint) {
    throw "Orchestration DB audit endpoint is not registered."
}

$payload = @{
    preferred_provider = "mock"
    fallback_providers = @()
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

$result = Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:8000/api/v1/llm-orchestration/run-with-db-audit" `
    -ContentType "application/json" `
    -Body $payload

$result | ConvertTo-Json -Depth 12

$traceId = $result.audit_trace.id

$readBack = Invoke-RestMethod `
    -Method Get `
    -Uri "http://localhost:8000/api/v1/llm-audit-traces/db/$traceId"

if ($readBack.id -ne $traceId) {
    throw "DB readback id mismatch for orchestration audit trace."
}

Write-Host ""
Write-Host "Orchestration DB audit readback verified."

Write-Host ""
Write-Host "=== RC29 Orchestration DB Audit Persistence Validation Passed ==="
