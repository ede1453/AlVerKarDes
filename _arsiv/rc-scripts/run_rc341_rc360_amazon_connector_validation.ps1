$ErrorActionPreference = "Stop"

$env:AMAZON_CREATORS_FIXTURE_MODE = "true"
$env:AMAZON_CREATORS_PARTNER_TAG = "example-21"
$env:AMAZON_CREATORS_CLIENT_ID = "fixture-client"
$env:AMAZON_CREATORS_CLIENT_SECRET = "fixture-secret"
$env:AMAZON_CREATORS_BASE_URL = "https://api.amazon.fixture"
$env:AMAZON_CREATORS_MARKETPLACE = "amazon.de"
$env:AMAZON_CREATORS_FIXTURE_PATH = "fixtures/amazon/search_response.json"

python -m pytest `
tests/test_rc341_amazon_configuration.py `
tests/test_rc342_amazon_token_cache.py `
tests/test_rc343_amazon_headers.py `
tests/test_rc344_amazon_search_request.py `
tests/test_rc345_amazon_item_request.py `
tests/test_rc346_amazon_product_normalization.py `
tests/test_rc347_amazon_offer_normalization.py `
tests/test_rc348_amazon_response_normalization.py `
tests/test_rc349_amazon_error_mapping.py `
tests/test_rc350_amazon_retry_delay.py `
tests/test_rc351_amazon_execution_retry.py `
tests/test_rc352_amazon_search_products.py `
tests/test_rc353_amazon_get_products.py `
tests/test_rc354_amazon_price_snapshots.py `
tests/test_rc355_amazon_deduplication.py `
tests/test_rc356_amazon_attribution.py `
tests/test_rc357_amazon_ingestion_records.py `
tests/test_rc358_amazon_metrics.py `
tests/test_rc359_amazon_health.py `
tests/test_rc360_amazon_end_to_end_collection.py `
tests/test_rc341_rc360_amazon_connector_api.py `
tests/test_rc341_rc360_amazon_connector_openapi.py -q

python -m py_compile app/domains/amazon_connector/service.py
python -m py_compile app/domains/amazon_connector/factory.py
python -m py_compile app/api/v1/amazon_connector_router.py
python -m py_compile scripts/check_amazon_connector_env.py
python -m py_compile scripts/run_amazon_fixture_smoke.py

python scripts/run_amazon_fixture_smoke.py
python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py
python scripts/api_contract_schema_guard.py
python -m pytest -q
