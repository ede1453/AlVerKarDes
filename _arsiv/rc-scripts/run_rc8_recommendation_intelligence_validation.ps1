$ErrorActionPreference = "Stop"

Write-Host "=== RC8 Recommendation Intelligence Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc8_recommendation_intelligence_engine.py tests/test_rc8_recommendation_intelligence_serializer.py -q

Write-Host ""
Write-Host "=== Full test suite ==="
python -m pytest -q

Write-Host ""
Write-Host "=== RC8 Recommendation Intelligence Validation Passed ==="
