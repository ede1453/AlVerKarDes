$ErrorActionPreference = "Stop"

Write-Host "=== RC56 Profile-Aware Recommendation Integration Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc56_profile_aware_recommendation_engine.py tests/test_rc56_profile_aware_recommendation_service.py tests/test_rc56_profile_aware_recommendation_api_contract.py tests/test_rc56_profile_aware_recommendation_openapi.py tests/test_rc56_profile_aware_recommendation_vertical_slice.py -q

Write-Host ""
Write-Host "=== Related profile/recommendation tests ==="
python -m pytest tests/test_rc55_user_profile_api_contract.py tests/test_rc52_recommendation_api_contract.py tests/test_rc54_user_activity_api_contract.py -q

Write-Host ""
Write-Host "=== OpenAPI uniqueness guard ==="
python scripts/check_openapi_uniqueness.py

Write-Host ""
Write-Host "=== API contract snapshot guard ==="
python scripts/api_contract_snapshot.py

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
Write-Host "=== Profile-aware recommendation API call ==="

$payload = @{
    user_id = "validation-user"
    query = "MacBook Air"
    profile_context = @{
        user_id = "validation-user"
        preferred_product_keys = @("macbook-air")
        preferred_marketplaces = @("saturn")
        preferred_brands = @("Apple")
        avoided_product_keys = @()
        blocked_marketplaces = @()
        risk_tolerance = "LOW"
        profile_score = 60
        metadata = @{ context_version = "user_profile_context_v1" }
    }
    candidates = @(
        @{
            product_key = "macbook-air"
            product_name = "Apple MacBook Air"
            marketplace = "saturn"
            price = "949.00"
        }
    )
} | ConvertTo-Json -Depth 12

Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/profile-aware-recommendations/recommend" -ContentType "application/json" -Body $payload | ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== RC56 Profile-Aware Recommendation Integration Validation Passed ==="
