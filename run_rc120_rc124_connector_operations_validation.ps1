$ErrorActionPreference = "Stop"

python -m pytest `
tests/test_rc120_connector_credentials.py `
tests/test_rc121_connector_schema_validation.py `
tests/test_rc122_connector_retry_backoff.py `
tests/test_rc123_connector_scheduler.py `
tests/test_rc124_connector_metrics.py `
tests/test_rc120_rc124_connector_operations_api.py `
tests/test_rc120_rc124_connector_operations_openapi.py -q

python -m py_compile app/domains/commerce_ingestion/operations.py
python -m py_compile app/api/v1/connector_operations_router.py

python scripts/check_docker_db_env_consistency.py
python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py
python scripts/api_contract_schema_guard.py
python -m pytest -q
