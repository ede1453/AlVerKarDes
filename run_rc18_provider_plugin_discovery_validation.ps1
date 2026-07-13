$ErrorActionPreference = "Stop"

Write-Host "=== RC18 Provider Plugin Discovery Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc18_provider_plugin_registry.py tests/test_rc18_provider_discovery.py tests/test_rc18_provider_registry_backward_compatibility.py tests/test_rc18_llm_gateway_plugin_vertical_slice.py -q

Write-Host ""
Write-Host "=== Existing LLM provider tests ==="
python -m pytest tests/test_rc15_llm_provider_registry.py tests/test_rc16_provider_registry.py tests/test_rc15_llm_provider_gateway_api_contract.py tests/test_rc16_llm_gateway_external_provider_api_contract.py -q

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
Write-Host "=== RC18 Provider Plugin Discovery Validation Passed ==="
