$ErrorActionPreference = "Stop"

Write-Host "=== Compose config ==="
docker compose -f docker-compose.prod.yml config | Out-Null

Write-Host "=== Python quality checks ==="
$Python = "python"
if (Test-Path ".\.venv\Scripts\python.exe") {
    $Python = ".\.venv\Scripts\python.exe"
}
& $Python -m ruff check app tests scripts
& $Python -m scripts.check_docker_db_env_consistency
& $Python -m pytest -q
Write-Host "=== Build containers ==="
docker compose -f docker-compose.prod.yml build

Write-Host "=== Start containers ==="
docker compose -f docker-compose.prod.yml up -d

Write-Host "=== Run migrations ==="
docker compose -f docker-compose.prod.yml exec aici-api alembic upgrade head

Write-Host "=== Health ==="
Invoke-RestMethod "http://localhost:8000/health" | ConvertTo-Json -Depth 10

Write-Host "=== Release Health ==="
Invoke-RestMethod "http://localhost:8000/api/v1/system/release-health" | ConvertTo-Json -Depth 12

Write-Host "=== RC1 PROD CHECK PASSED ==="

