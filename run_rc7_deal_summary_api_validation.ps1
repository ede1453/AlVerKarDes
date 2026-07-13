$ErrorActionPreference = "Stop"

Write-Host "=== RC7 Deal Summary API Validation ==="

Write-Host ""
Write-Host "=== Python tests ==="
python -m pytest tests/test_rc7_deal_summary_api_contract.py tests/test_rc7_deal_summary_api_response.py -q
python -m pytest -q

Write-Host ""
Write-Host "=== Docker rebuild ==="
docker compose -f docker-compose.prod.yml up -d --build --force-recreate

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
    Write-Host ""
    Write-Host "=== API logs ==="
    docker compose -f docker-compose.prod.yml logs --tail=120 aici-api
    throw "API did not become ready."
}

Write-Host ""
Write-Host "=== API health ==="
Invoke-RestMethod "http://localhost:8000/health" | ConvertTo-Json -Depth 10

Write-Host ""
Write-Host "=== OpenAPI check ==="
Invoke-RestMethod "http://localhost:8000/openapi.json" |
ConvertTo-Json -Depth 8 |
Select-String "/api/v1/deals/summary"

Write-Host ""
Write-Host "=== Deal Summary API call ==="

$payload = @{
    prices = @(
        @{
            amount = "899.00"
            observed_at = "2026-06-15T00:00:00+00:00"
        },
        @{
            amount = "849.00"
            observed_at = "2026-07-05T00:00:00+00:00"
        }
    )
    cross_store_min_amount = "849.00"
    store_trust_score = 95
    stock_status = "in_stock"
} | ConvertTo-Json -Depth 10

try {
    Invoke-RestMethod `
        -Method Post `
        -Uri "http://localhost:8000/api/v1/deals/summary" `
        -ContentType "application/json" `
        -Body $payload |
    ConvertTo-Json -Depth 12
}
catch {
    Write-Host ""
    Write-Host "=== API request failed. Recent API logs ==="
    docker compose -f docker-compose.prod.yml logs --tail=160 aici-api
    throw
}

Write-Host ""
Write-Host "=== RC7 Deal Summary API Validation Passed ==="
