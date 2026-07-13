#!/usr/bin/env bash
set -euo pipefail

API_BASE="${API_BASE:-http://localhost:8000/api/v1}"

echo "Health"
curl -s http://localhost:8000/health
echo

echo "Create product"
PRODUCT_RESPONSE=$(curl -s -X POST "$API_BASE/products/from-name?product_name=Apple%20MacBook%20Air%20M5%2016GB%20512GB&country=DE")
echo "$PRODUCT_RESPONSE"
PRODUCT_ID=$(echo "$PRODUCT_RESPONSE" | python -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Create store"
STORE_RESPONSE=$(curl -s -X POST "$API_BASE/market/stores" \
  -H "Content-Type: application/json" \
  -d '{"name":"Amazon Germany","slug":"amazon-de","website":"https://www.amazon.de","country":"DE","affiliate_enabled":true,"trust_score":85}')
echo "$STORE_RESPONSE"
STORE_ID=$(echo "$STORE_RESPONSE" | python -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Create offer"
OFFER_RESPONSE=$(curl -s -X POST "$API_BASE/market/offers" \
  -H "Content-Type: application/json" \
  -d "{\"product_id\":\"$PRODUCT_ID\",\"store_id\":\"$STORE_ID\",\"url\":\"https://www.amazon.de/example-macbook-air-m5\",\"store_sku\":\"AMZ-MBA-M5-16-512\",\"title_on_store\":\"Apple MacBook Air M5 16GB 512GB\"}")
echo "$OFFER_RESPONSE"
OFFER_ID=$(echo "$OFFER_RESPONSE" | python -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Add price snapshots"
for PRICE in 1199 1099 999 949 899 849; do
  curl -s -X POST "$API_BASE/market/prices" \
    -H "Content-Type: application/json" \
    -d "{\"offer_id\":\"$OFFER_ID\",\"amount\":$PRICE,\"currency\":\"EUR\",\"source\":\"manual\"}"
  echo
done

echo "Analyze"
curl -s -X POST "$API_BASE/recommendations/analyze" \
  -H "Content-Type: application/json" \
  -d "{
    \"product_name\":\"Apple MacBook Air M5 16GB 512GB\",
    \"offer_id\":\"$OFFER_ID\",
    \"user_context\":{
      \"country\":\"DE\",
      \"currency\":\"EUR\",
      \"offer_url\":\"https://www.amazon.de/example-macbook-air-m5\",
      \"store_name\":\"Amazon Germany\",
      \"store_trust_score\":85,
      \"reviews\":[
        \"Great performance but battery life is poor.\",
        \"The screen is excellent, but the battery drains fast.\",
        \"Very good build quality.\",
        \"Fast and reliable for university work.\",
        \"Battery could be better.\",
        \"Excellent keyboard and solid design.\"
      ]
    }
  }" | python -m json.tool
