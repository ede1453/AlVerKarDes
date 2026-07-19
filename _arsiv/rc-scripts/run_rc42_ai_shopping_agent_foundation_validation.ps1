$ErrorActionPreference = "Stop"

Write-Host "=== RC42 AI Shopping Agent Foundation Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc42_ai_shopping_agent_engine.py tests/test_rc42_ai_shopping_agent_service.py tests/test_rc42_ai_shopping_agent_api_contract.py tests/test_rc42_ai_shopping_agent_openapi.py tests/test_rc42_ai_shopping_agent_vertical_slice.py -q

Write-Host ""
Write-Host "=== Related intelligence stack tests ==="
python -m pytest tests/test_rc38_unified_search_api_contract.py tests/test_rc39_product_matching_api_contract.py tests/test_rc40_price_history_api_contract.py tests/test_rc41_personalization_api_contract.py -q

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
Write-Host "=== AI Shopping Agent API call ==="

$payload = @{
    query = "MacBook Air"
    user_id = "validation-user"
    profile = @{
        preferred_marketplaces = @("saturn")
        preferred_brands = @("Apple")
        max_price = "1000.00"
    }
    offers = @(
        @{ id = "1"; marketplace = "amazon"; seller = "Amazon"; product_name = "Apple MacBook Air M3"; price = "999.00"; currency = "EUR" },
        @{ id = "2"; marketplace = "saturn"; seller = "Saturn"; product_name = "Apple MacBook Air M3"; price = "949.00"; currency = "EUR" }
    )
} | ConvertTo-Json -Depth 12

Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/ai-shopping-agent/run" -ContentType "application/json" -Body $payload | ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== RC42 AI Shopping Agent Foundation Validation Passed ==="
