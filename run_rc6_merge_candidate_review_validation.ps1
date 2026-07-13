$ErrorActionPreference = "Stop"

Write-Host "=== RC6 Merge Candidate Review Validation ==="

Write-Host ""
Write-Host "=== Python tests ==="
python -m pytest tests/test_rc6_merge_candidate_review_service.py tests/test_rc6_merge_candidate_review_api_contract.py -q
python -m pytest -q

Write-Host ""
Write-Host "=== Docker rebuild ==="
docker compose -f docker-compose.prod.yml up -d --build --force-recreate

Write-Host ""
Write-Host "=== Alembic upgrade ==="
docker compose -f docker-compose.prod.yml exec aici-api alembic upgrade head

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
Write-Host "=== Persist merge candidate ==="

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

$persist = Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:8000/api/v1/products/intelligence/merge-candidates/persist" `
    -ContentType "application/json" `
    -Body $payload

$persist | ConvertTo-Json -Depth 12

$candidateId = $persist.saved_ids[0]

Write-Host ""
Write-Host "=== Review merge candidate APPROVED ==="

$reviewPayload = @{
    status = "APPROVED"
} | ConvertTo-Json -Depth 10

Invoke-RestMethod `
    -Method Patch `
    -Uri "http://localhost:8000/api/v1/products/intelligence/merge-candidates/$candidateId/review" `
    -ContentType "application/json" `
    -Body $reviewPayload |
ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== Inspect reviewed candidate ==="
docker compose -f docker-compose.prod.yml exec aici-db psql -U postgres -d aici -c "select id, signature, decision, status, reviewed_at from merge_candidates where id = '$candidateId';"

Write-Host ""
Write-Host "=== RC6 Merge Candidate Review Validation Passed ==="
