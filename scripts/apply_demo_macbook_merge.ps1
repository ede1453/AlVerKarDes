$ErrorActionPreference = "Stop"

Write-Host "=== Find active MacBook products ==="

$rows = docker exec aici-db-prod psql -U postgres -d aici -t -A -F "," -c "select id, canonical_key from products where deleted_at is null and canonical_key like '%m5%' order by created_at;"

if (-not $rows) {
    throw "No active M5 products found."
}

$products = @()

foreach ($row in $rows) {
    $parts = $row.Split(",", 2)
    if ($parts.Length -eq 2) {
        $products += [PSCustomObject]@{
            id = $parts[0].Trim()
            canonical_key = $parts[1].Trim()
        }
    }
}

if ($products.Count -lt 2) {
    Write-Host "No merge needed. Active M5 product count: $($products.Count)"
    exit 0
}

$master = $products | Where-Object { $_.canonical_key -like "*macbook-air*" } | Select-Object -First 1

if (-not $master) {
    $master = $products | Select-Object -First 1
}

$duplicates = $products | Where-Object { $_.id -ne $master.id }

Write-Host "Master: $($master.id) $($master.canonical_key)"
Write-Host "Duplicates:"
$duplicates | ForEach-Object { Write-Host "- $($_.id) $($_.canonical_key)" }

$mergeBody = @{
    merge_plan = @{
        master_product_id = $master.id
        duplicate_product_ids = @(
            $duplicates | ForEach-Object { $_.id }
        )
    }
} | ConvertTo-Json -Depth 10

Write-Host ""
Write-Host "=== Apply merge ==="
$mergeResult = Invoke-RestMethod `
    -Method Post `
    "http://localhost:8000/api/v1/products/merge/apply" `
    -ContentType "application/json" `
    -Body $mergeBody

$mergeResult | ConvertTo-Json -Depth 10

Write-Host ""
Write-Host "=== Verify merge ==="

$verifyBody = @{
    master_product_id = $master.id
    duplicate_product_ids = @($duplicates | ForEach-Object { $_.id })
} | ConvertTo-Json -Depth 10

$verifyResult = Invoke-RestMethod `
    -Method Post `
    "http://localhost:8000/api/v1/products/merge/verify" `
    -ContentType "application/json" `
    -Body $verifyBody

$verifyResult | ConvertTo-Json -Depth 10

if ($verifyResult.passed -ne $true) {
    throw "Merge verification failed."
}

Write-Host ""
Write-Host "=== Release health ==="
$release = Invoke-RestMethod "http://localhost:8000/api/v1/system/release-health"
$release | ConvertTo-Json -Depth 12

if ($release.passed -ne $true) {
    throw "Release health failed after merge."
}

Write-Host ""
Write-Host "=== Merge flow complete ==="
