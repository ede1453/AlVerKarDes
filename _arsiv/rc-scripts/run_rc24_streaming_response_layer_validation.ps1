$ErrorActionPreference = "Stop"

Write-Host "=== RC24 Streaming Response Layer Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc24_streaming_engine.py tests/test_rc24_sse_formatter.py tests/test_rc24_streaming_service.py tests/test_rc24_streaming_api_contract.py tests/test_rc24_streaming_openapi.py tests/test_rc24_streaming_vertical_slice.py -q

Write-Host ""
Write-Host "=== Related orchestration tests ==="
python -m pytest tests/test_rc23_retry_backoff_vertical_slice.py tests/test_rc19_llm_orchestration_api_contract.py -q

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
Write-Host "=== Streaming preview API call ==="

$payload = @{
    text = "MacBook Air is a buy-now candidate based on the provided signals."
    chunk_size = 16
    metadata = @{
        source = "validation"
    }
} | ConvertTo-Json -Depth 12

Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:8000/api/v1/llm-streaming/preview" `
    -ContentType "application/json" `
    -Body $payload |
ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== RC24 Streaming Response Layer Validation Passed ==="
