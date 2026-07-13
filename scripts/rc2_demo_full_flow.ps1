$ErrorActionPreference = "Stop"

Write-Host "=== RC2 demo full flow ==="

powershell -ExecutionPolicy Bypass -File .\scripts\seed_demo_connectors.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\apply_demo_macbook_merge.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\inspect_prod_data.ps1

Write-Host ""
Write-Host "=== Final release health ==="
Invoke-RestMethod "http://localhost:8000/api/v1/system/release-health" | ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== RC2 demo full flow passed ==="
