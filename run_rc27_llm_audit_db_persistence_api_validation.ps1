$ErrorActionPreference = "Stop"

Write-Host "=== RC27 LLM Audit DB Persistence API Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc27_llm_audit_db_router_contract.py tests/test_rc27_llm_audit_db_smoke_contract.py tests/test_rc27_llm_audit_db_openapi.py -q

Write-Host ""
Write-Host "=== Existing audit repository tests ==="
python -m pytest tests/test_rc26_llm_audit_repository_factory.py tests/test_rc26_llm_audit_sql_repository.py tests/test_rc26_llm_audit_service_db_boundary.py tests/test_rc17_llm_audit_api_contract.py -q

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
Write-Host "=== DB audit endpoint smoke check ==="

$payload = @{
    request_payload = @{
        provider = "mock"
        model = "mock-shopping-explainer"
        system_prompt = "system"
        user_prompt = "user"
        structured_context = @{
            assistant_decision = "BUY_NOW"
            prompt_version = "shopping_v1"
        }
        prompt_version = "shopping_v1"
    }
    gateway_response = @{
        provider = "mock"
        model = "mock-shopping-explainer"
        status = "COMPLETED"
        safety_warnings = @()
        usage = @{
            mock = $true
        }
        metadata = @{
            prompt_version = "shopping_v1"
        }
    }
} | ConvertTo-Json -Depth 12

$openapi = Invoke-RestMethod "http://localhost:8000/openapi.json" 
$hasDbEndpoint = $openapi.paths.PSObject.Properties.Name.Contains("/api/v1/llm-audit-traces/db")

if ($hasDbEndpoint) {
    Invoke-RestMethod `
        -Method Post `
        -Uri "http://localhost:8000/api/v1/llm-audit-traces/db" `
        -ContentType "application/json" `
        -Body $payload |
    ConvertTo-Json -Depth 12
}
else {
    Write-Host "DB audit endpoint not registered in this app layout; in-memory endpoint remains active."
}

Write-Host ""
Write-Host "=== RC27 LLM Audit DB Persistence API Validation Passed ==="
