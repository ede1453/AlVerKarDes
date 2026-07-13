$ErrorActionPreference = "Stop"

Write-Host "=== Products ==="
docker exec -it aici-db-prod psql -U postgres -d aici -c "select id, deleted_at, canonical_key from products order by created_at;"

Write-Host "=== Offers by product ==="
docker exec -it aici-db-prod psql -U postgres -d aici -c "select product_id, count(*) from offers group by product_id order by count(*) desc;"

Write-Host "=== Prices ==="
docker exec -it aici-db-prod psql -U postgres -d aici -c "select offer_id, amount, currency, stock_status, created_at from prices order by created_at desc limit 20;"
