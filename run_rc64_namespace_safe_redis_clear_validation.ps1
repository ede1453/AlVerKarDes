$ErrorActionPreference = "Stop"

Write-Host "=== RC64 Namespace Safe Redis Clear Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc64_redis_namespace_safe_clear.py tests/test_rc64_cache_clear_api_contract.py -q

Write-Host ""
Write-Host "=== Related cache namespace tests ==="
python -m pytest tests/test_rc63_cache_namespace.py tests/test_rc63_redis_cache_repository_namespace_contract.py tests/test_rc62_cache_backend_api_activation.py tests/test_rc61_redis_cache_repository.py -q

Write-Host ""
Write-Host "=== Existing guards ==="
python scripts/check_docker_db_env_consistency.py
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
Write-Host "=== Cache set/get/clear smoke ==="
$payload = @{
    key = "rc64:docker:cache"
    value = @{ status = "ok" }
    ttl_seconds = 60
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/cache/set" -ContentType "application/json" -Body $payload | ConvertTo-Json -Depth 12

$cacheReadPayload = @{
    key = "rc64:docker:cache"
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/cache/get" -ContentType "application/json" -Body $cacheReadPayload | ConvertTo-Json -Depth 12

Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/cache/clear" | ConvertTo-Json -Depth 12

Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/cache/get" -ContentType "application/json" -Body $cacheReadPayload | ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== RC64 Namespace Safe Redis Clear Validation Passed ==="
