$ErrorActionPreference = "Stop"

Write-Host "=== RC62 Redis Backend API Activation Guard Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc62_cache_backend_api_activation.py tests/test_rc62_runtime_settings_cache_backend_contract.py tests/test_rc62_docker_compose_redis_env_contract.py -q

Write-Host ""
Write-Host "=== Related cache/runtime/docker tests ==="
python -m pytest tests/test_rc61_cache_repository_factory.py tests/test_rc61_redis_cache_repository.py tests/test_rc611_redis_backend_runtime_config.py tests/test_rc614_docker_db_env_consistency_guard.py -q

Write-Host ""
Write-Host "=== Docker DB env consistency guard ==="
python scripts/check_docker_db_env_consistency.py

Write-Host ""
Write-Host "=== Existing guards ==="
python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py
python scripts/api_contract_schema_guard.py

Write-Host ""
Write-Host "=== Full test suite ==="
python -m pytest -q

Write-Host ""
Write-Host "=== Docker clean rebuild ==="
docker compose -f docker-compose.prod.yml down --remove-orphans
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
Write-Host "=== Runtime settings smoke ==="
Invoke-RestMethod -Method Get -Uri "http://localhost:8000/api/v1/runtime-settings/status" | ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== Cache status smoke ==="
Invoke-RestMethod -Method Get -Uri "http://localhost:8000/api/v1/cache/status" | ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== Cache set/get smoke ==="
$payload = @{
    key = "rc62:docker:cache"
    value = @{ status = "ok" }
    ttl_seconds = 60
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/cache/set" -ContentType "application/json" -Body $payload | ConvertTo-Json -Depth 12
$cacheReadPayload = @{
    key = "rc62:docker:cache"
} | ConvertTo-Json -Depth 10

Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:8000/api/v1/cache/get" `
    -ContentType "application/json" `
    -Body $cacheReadPayload | ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== RC62 Redis Backend API Activation Guard Validation Passed ==="
