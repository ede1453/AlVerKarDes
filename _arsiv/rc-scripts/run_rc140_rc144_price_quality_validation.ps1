$ErrorActionPreference = "Stop"

python -m pytest `
tests/test_rc140_price_anomaly_detection.py `
tests/test_rc141_price_freshness.py `
tests/test_rc142_currency_normalization.py `
tests/test_rc143_source_trust_reconciliation.py `
tests/test_rc144_best_offer_aggregation.py `
tests/test_rc140_rc144_price_quality_api.py `
tests/test_rc140_rc144_price_quality_openapi.py -q

python -m py_compile app/domains/commerce_ingestion/price_quality.py
python -m py_compile app/api/v1/price_quality_router.py

python scripts/check_docker_db_env_consistency.py
python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py
python scripts/api_contract_schema_guard.py
python -m pytest -q
