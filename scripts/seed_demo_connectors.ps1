$ErrorActionPreference = "Stop"

Write-Host "=== Seed demo connector data ==="

$queries = @("M5", "Apple MacBook", "Sony WH-1000XM7")

foreach ($query in $queries) {
    Write-Host ""
    Write-Host "Ingest query: $query"

    $encoded = [System.Uri]::EscapeDataString($query)

    Invoke-RestMethod `
        -Method Post `
        "http://localhost:8000/api/v1/connectors/ingest?query=$encoded&country=DE" `
        | ConvertTo-Json -Depth 10
}

Write-Host ""
Write-Host "=== Verify release health ==="
Invoke-RestMethod "http://localhost:8000/api/v1/system/release-health" | ConvertTo-Json -Depth 12

Write-Host ""
Write-Host "=== Demo connector seed complete ==="
