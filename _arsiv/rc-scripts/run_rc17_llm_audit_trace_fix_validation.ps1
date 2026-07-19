$ErrorActionPreference = "Stop"

Write-Host "=== RC17 LLM Audit Trace FastAPI Query Fix Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc17_prompt_hashing.py tests/test_rc17_llm_audit_repository.py tests/test_rc17_llm_audit_service.py tests/test_rc17_llm_audit_api_contract.py tests/test_rc17_llm_audit_openapi.py tests/test_rc17_llm_audit_vertical_slice.py tests/test_rc17_llm_audit_fastapi_query_param_contract.py -q

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
Write-Host "=== LLM Audit Trace list query check ==="

Invoke-RestMethod `
    -Method Get `
    -Uri "http://localhost:8000/api/v1/llm-audit-traces?limit=5" |
ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== RC17 LLM Audit Trace FastAPI Query Fix Validation Passed ==="
