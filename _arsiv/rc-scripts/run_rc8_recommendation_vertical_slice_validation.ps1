$ErrorActionPreference = "Stop"

Write-Host "=== RC8 Recommendation Vertical Slice Validation ==="

Write-Host ""
Write-Host "=== Targeted tests ==="
python -m pytest tests/test_rc8_recommendation_api_contract.py tests/test_rc8_recommendation_service.py tests/test_rc8_recommendation_vertical_slice.py -q

Write-Host ""
Write-Host "=== Full test suite ==="
python -m pytest -q

Write-Host ""
Write-Host "=== RC8 Recommendation Vertical Slice Validation Passed ==="
