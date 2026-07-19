$ErrorActionPreference = "Stop"

Write-Host "=== RC52.2 Recommendation OperationId Compatibility Validation ==="

Write-Host ""
Write-Host "=== OperationId compatibility tests ==="
python -m pytest tests/test_rc522_recommendation_operation_id_compatibility.py tests/test_rc521_recommendation_backward_compatibility.py -q

Write-Host ""
Write-Host "=== OpenAPI uniqueness guard ==="
python scripts/check_openapi_uniqueness.py

Write-Host ""
Write-Host "=== API contract snapshot guard ==="
python scripts/api_contract_snapshot.py

Write-Host ""
Write-Host "=== RC52 targeted tests ==="
python -m pytest tests/test_rc52_recommendation_engine.py tests/test_rc52_recommendation_service.py tests/test_rc52_recommendation_api_contract.py tests/test_rc52_recommendation_openapi.py tests/test_rc52_recommendation_vertical_slice.py -q

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
Write-Host "=== Legacy operationId smoke ==="

$openapi = Invoke-RestMethod -Method Get -Uri "http://localhost:8000/openapi.json"

$analyzeOperationId = $openapi.paths."/api/v1/recommendations/analyze".post.operationId
$sessionOperationId = $openapi.paths."/api/v1/recommendations/sessions/{session_id}".get.operationId

Write-Host "Analyze operationId: $analyzeOperationId"
Write-Host "Session operationId: $sessionOperationId"

if ($analyzeOperationId -ne "analyze_product_api_v1_recommendations_analyze_post") {
    throw "Legacy analyze operationId mismatch."
}

if ($sessionOperationId -ne "get_session_recommendations_api_v1_recommendations_sessions__session_id__get") {
    throw "Legacy session operationId mismatch."
}

Write-Host ""
Write-Host "=== RC52.2 Recommendation OperationId Compatibility Validation Passed ==="
