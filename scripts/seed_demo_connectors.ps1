$ErrorActionPreference = "Stop"

Write-Host "=== Seed demo connector data ==="

# PARÇA B (ADR-007): connector'lar artık gerçek (ya da fixture-mode)
# Amazon/eBay/Idealo servislerinden geliyor -- fixture verisi "Example
# Laptop" olduğu için sorgu buna göre güncellendi.
$queries = @("Example Laptop")

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
