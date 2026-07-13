$ErrorActionPreference = "Stop"

Write-Host "=== RC6 Merge Candidate API Validation ==="

Write-Host ""
Write-Host "=== Python tests ==="
python -m pytest tests/test_rc6_merge_candidate_service.py tests/test_rc6_merge_candidate_api_contract.py -q
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
    throw "API did not become ready."
}

Write-Host ""
Write-Host "=== OpenAPI check ==="
Invoke-RestMethod "http://localhost:8000/openapi.json" |
ConvertTo-Json -Depth 8 |
Select-String "/api/v1/products/intelligence/merge-candidates"

Write-Host ""
Write-Host "=== Merge candidate API call ==="

$payload = @{
    country = "DE"
    offers = @(
        @{
            source = "amazon-de"
            title = "Apple MacBook Air M5 16GB 512GB Midnight"
            url = "https://www.amazon.de/dp/B0M5AIR16512"
            sku = "B0M5AIR16512"
        },
        @{
            source = "mediamarkt-de"
            title = "Apple MBA M5 16/512 Silver"
            url = "https://www.mediamarkt.de/de/product/_apple-macbook-air-m5-16-512.html"
            sku = "MM-MBA-M5-16-512"
        }
    )
} | ConvertTo-Json -Depth 10

Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:8000/api/v1/products/intelligence/merge-candidates" `
    -ContentType "application/json" `
    -Body $payload |
ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== RC6 Merge Candidate API Validation Passed ==="
