$ErrorActionPreference = "Stop"

python -m pytest `
tests/test_rc105_connector_source_registry.py `
tests/test_rc106_raw_offer_collection.py `
tests/test_rc107_offer_normalization.py `
tests/test_rc108_price_snapshot_ingestion.py `
tests/test_rc109_connector_run_health.py `
tests/test_rc105_rc109_commerce_ingestion_api.py `
tests/test_rc105_rc109_commerce_ingestion_openapi.py -q

python -m py_compile app/domains/commerce_ingestion/service.py
python -m py_compile app/api/v1/commerce_ingestion_router.py
python scripts/check_docker_db_env_consistency.py
python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py
python scripts/api_contract_schema_guard.py
python -m pytest -q
