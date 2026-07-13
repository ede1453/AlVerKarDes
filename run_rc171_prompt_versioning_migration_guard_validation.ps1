$ErrorActionPreference = "Stop"

Write-Host "=== RC17.1 Prompt Versioning + Migration Guard Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc171_prompt_versioning.py tests/test_rc171_llm_audit_prompt_version.py tests/test_rc171_alembic_linear_history.py -q

Write-Host ""
Write-Host "=== Alembic linear history script ==="
python scripts/check_alembic_linear_history.py

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
Write-Host "=== Prompt version API check ==="

$payload = @{
    assistant_decision = "BUY_NOW"
    headline = "Buy MacBook Air now"
    summary = "The combined decision supports buying now."
    confidence = 94
    assistant_context = @{
        product_name = "MacBook Air"
    }
    prompt_version = "shopping_v1"
} | ConvertTo-Json -Depth 12

Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:8000/api/v1/llm-explanations/prepare" `
    -ContentType "application/json" `
    -Body $payload |
ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== RC17.1 Prompt Versioning + Migration Guard Validation Passed ==="
