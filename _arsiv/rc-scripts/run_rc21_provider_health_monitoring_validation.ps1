$ErrorActionPreference = "Stop"

Write-Host "=== RC21 Provider Health Monitoring Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc21_provider_health_probe.py tests/test_rc21_provider_health_engine.py tests/test_rc21_provider_health_service.py tests/test_rc21_provider_health_api_contract.py tests/test_rc21_provider_health_openapi.py tests/test_rc21_provider_health_vertical_slice.py -q

Write-Host ""
Write-Host "=== Related provider/orchestration tests ==="
python -m pytest tests/test_rc18_provider_registry_backward_compatibility.py tests/test_rc19_llm_orchestration_api_contract.py tests/test_rc20_orchestration_audit_api_contract.py -q

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
Write-Host "=== Provider health summary API call ==="

Invoke-RestMethod `
    -Method Get `
    -Uri "http://localhost:8000/api/v1/llm-provider-health/summary" |
ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== RC21 Provider Health Monitoring Validation Passed ==="
