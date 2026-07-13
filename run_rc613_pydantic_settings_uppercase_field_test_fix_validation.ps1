$ErrorActionPreference = "Stop"

Write-Host "=== RC61.3 Pydantic Settings Uppercase Field Test Fix Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc612_pydantic_settings_redis_env_compatibility.py tests/test_rc612_app_import_with_redis_env.py tests/test_rc613_pydantic_settings_uppercase_field_contract.py -q

Write-Host ""
Write-Host "=== Runtime/cache tests ==="
python -m pytest tests/test_rc611_redis_backend_runtime_config.py tests/test_rc611_cache_repository_factory_redis_selection.py tests/test_rc61_cache_repository_factory.py tests/test_rc61_redis_cache_repository.py tests/test_rc60_runtime_settings_api_contract.py tests/test_rc601_runtime_settings_external_providers_env_fix.py -q

Write-Host ""
Write-Host "=== Existing guards ==="
python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py
python scripts/api_contract_schema_guard.py

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
Write-Host "=== RC61.3 Pydantic Settings Uppercase Field Test Fix Validation Passed ==="
