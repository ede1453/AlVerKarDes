$ErrorActionPreference = "Stop"

Write-Host "=== RC5 Final Validation ==="

Write-Host ""
Write-Host "=== Python tests ==="
python -m pytest -q

Write-Host ""
Write-Host "=== Docker production rebuild ==="
docker compose -f docker-compose.prod.yml up -d --build --force-recreate

Write-Host ""
Write-Host "=== Alembic upgrade ==="
docker compose -f docker-compose.prod.yml exec aici-api alembic upgrade head

Write-Host ""
Write-Host "=== Wait for API readiness ==="

$ready = $false

for ($i = 1; $i -le 30; $i++) {
    try {
        $health = Invoke-RestMethod "http://localhost:8000/health"
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
Write-Host "=== API health ==="
Invoke-RestMethod "http://localhost:8000/health" | ConvertTo-Json -Depth 10

Write-Host ""
Write-Host "=== Release health ==="
Invoke-RestMethod "http://localhost:8000/api/v1/system/release-health" | ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== External connector search ==="
Invoke-RestMethod "http://localhost:8000/api/v1/external-connectors/search?query=M5&country=DE" | ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== External connector ingest ==="
Invoke-RestMethod -Method Post "http://localhost:8000/api/v1/external-connectors/ingest?query=M5&country=DE" | ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== RC5 Final Validation Passed ==="
