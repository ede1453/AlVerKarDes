$ErrorActionPreference = "Stop"

Write-Host "=== RC11 Feedback Learning Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc11_feedback_engine.py tests/test_rc11_feedback_learning_engine.py tests/test_rc11_feedback_repository.py tests/test_rc11_feedback_service.py tests/test_rc11_feedback_api_contract.py tests/test_rc11_feedback_openapi.py -q

Write-Host ""
Write-Host "=== Full test suite ==="
python -m pytest -q

Write-Host ""
Write-Host "=== Docker rebuild ==="
docker compose -f docker-compose.prod.yml up -d --build --force-recreate

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
Write-Host "=== OpenAPI registration check ==="
Invoke-RestMethod "http://localhost:8000/openapi.json" |
ConvertTo-Json -Depth 8 |
Select-String "/api/v1/feedback-learning/feedback"

Write-Host ""
Write-Host "=== Feedback Learning API call ==="

$payload = @{
    user_id = "user-1"
    decision_id = "decision-1"
    feedback_type = "HELPFUL"
    rating = 5
} | ConvertTo-Json -Depth 10

$saved = Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:8000/api/v1/feedback-learning/feedback" `
    -ContentType "application/json" `
    -Body $payload

$saved | ConvertTo-Json -Depth 12

Invoke-RestMethod `
    -Method Get `
    -Uri "http://localhost:8000/api/v1/feedback-learning/users/user-1/summary" |
ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== RC11 Feedback Learning Validation Passed ==="
