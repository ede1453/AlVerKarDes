param(
    [string]$ApiBase = "http://localhost:8000"
)

$ErrorActionPreference = "Stop"

function Write-Step($Message) {
    Write-Host ""
    Write-Host "=== $Message ==="
}

Write-Step "Python tests"
$env:PYTHONPATH="."
python -m pytest -q

Write-Step "API health"
$health = Invoke-RestMethod "$ApiBase/health"
$health | ConvertTo-Json -Depth 10

if ($health.status -ne "ok") {
    throw "Health check failed."
}

Write-Step "Data integrity"
$integrity = Invoke-RestMethod "$ApiBase/api/v1/integrity/check"
$integrity | ConvertTo-Json -Depth 10

if ($integrity.passed -ne $true) {
    throw "Integrity check failed."
}

Write-Step "Duplicate product regression"
$duplicateRegression = Invoke-RestMethod "$ApiBase/api/v1/integrity/duplicate-product-regression"
$duplicateRegression | ConvertTo-Json -Depth 10

if ($duplicateRegression.passed -ne $true) {
    throw "Duplicate product regression check failed."
}

Write-Step "Release health"
$release = Invoke-RestMethod "$ApiBase/api/v1/system/release-health"
$release | ConvertTo-Json -Depth 12

if ($release.passed -ne $true) {
    throw "Release health failed."
}

Write-Step "Validation result"
Write-Host "LOCAL VALIDATION PASSED"
