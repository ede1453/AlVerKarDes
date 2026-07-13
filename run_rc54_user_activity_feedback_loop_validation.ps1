$ErrorActionPreference = "Stop"

Write-Host "=== RC54 User Activity Feedback Loop Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc54_user_activity_engine.py tests/test_rc54_user_activity_service.py tests/test_rc54_user_activity_api_contract.py tests/test_rc54_user_activity_openapi.py tests/test_rc54_user_activity_vertical_slice.py -q

Write-Host ""
Write-Host "=== Related recommendation/personalization tests ==="
python -m pytest tests/test_rc52_recommendation_api_contract.py tests/test_rc41_personalization_api_contract.py tests/test_rc53_notification_api_contract.py -q

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
Write-Host "=== User activity API call ==="

$payload = @{
    user_id = "validation-user"
    event_type = "recommendation_clicked"
    product_key = "macbook-air"
} | ConvertTo-Json -Depth 12

Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/user-activity/record" -ContentType "application/json" -Body $payload | ConvertTo-Json -Depth 12

Invoke-RestMethod -Method Get -Uri "http://localhost:8000/api/v1/user-activity/users/validation-user/summary" | ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== RC54 User Activity Feedback Loop Validation Passed ==="
