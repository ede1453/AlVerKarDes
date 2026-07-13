$ErrorActionPreference = "Stop"
$API_BASE = "http://localhost:8000/api/v1"

Write-Host "=== Health Check ==="
Invoke-RestMethod "http://localhost:8000/health"

Write-Host "`n=== Create Product ==="
$product = Invoke-RestMethod -Method Post "$API_BASE/products/from-name?product_name=Apple%20MacBook%20Air%20M5%2016GB%20512GB&country=DE"
$productId = $product.id
Write-Host "Product ID: $productId"

Write-Host "`n=== Create Store ==="
$storeBody = @{
    name = "Amazon Germany"
    slug = "amazon-de"
    website = "https://www.amazon.de"
    country = "DE"
    affiliate_enabled = $true
    trust_score = 85
} | ConvertTo-Json

$store = Invoke-RestMethod -Method Post "$API_BASE/market/stores" -ContentType "application/json" -Body $storeBody
$storeId = $store.id
Write-Host "Store ID: $storeId"

Write-Host "`n=== Create Offer ==="
$offerBody = @{
    product_id = $productId
    store_id = $storeId
    url = "https://www.amazon.de/example-macbook-air-m5"
    store_sku = "AMZ-MBA-M5-16-512"
    title_on_store = "Apple MacBook Air M5 16GB 512GB"
} | ConvertTo-Json

$offer = Invoke-RestMethod -Method Post "$API_BASE/market/offers" -ContentType "application/json" -Body $offerBody
$offerId = $offer.id
Write-Host "Offer ID: $offerId"

Write-Host "`n=== Add Prices ==="
$prices = @(1199, 1099, 999, 949, 899, 849)

foreach ($price in $prices) {
    $priceBody = @{
        offer_id = $offerId
        amount = $price
        currency = "EUR"
        source = "manual"
    } | ConvertTo-Json

    Invoke-RestMethod -Method Post "$API_BASE/market/prices" -ContentType "application/json" -Body $priceBody | Out-Null
    Write-Host "Added price: $price EUR"
}

Write-Host "`n=== Analyze ==="
$analysisBody = @{
    product_name = "Apple MacBook Air M5 16GB 512GB"
    offer_id = $offerId
    user_context = @{
        country = "DE"
        currency = "EUR"
        offer_url = "https://www.amazon.de/example-macbook-air-m5"
        store_name = "Amazon Germany"
        store_trust_score = 85
        reviews = @(
            "Great performance but battery life is poor.",
            "The screen is excellent, but the battery drains fast.",
            "Very good build quality.",
            "Fast and reliable for university work.",
            "Battery could be better.",
            "Excellent keyboard and solid design."
        )
    }
} | ConvertTo-Json -Depth 10

$result = Invoke-RestMethod -Method Post "$API_BASE/recommendations/analyze" -ContentType "application/json" -Body $analysisBody
$result | ConvertTo-Json -Depth 10
