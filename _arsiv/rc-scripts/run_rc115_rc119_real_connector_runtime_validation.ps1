$ErrorActionPreference = "Stop"

python -m pytest `
tests/test_rc115_source_adapters.py `
tests/test_rc116_connector_runtime_execution.py `
tests/test_rc117_price_history_bridge.py `
tests/test_rc118_ingestion_idempotency.py `
tests/test_rc119_connector_observability.py `
tests/test_rc115_rc119_connector_runtime_api.py `
tests/test_rc115_rc119_connector_runtime_openapi.py -q

python -m py_compile app/domains/commerce_ingestion/source_adapters.py
python -m py_compile app/domains/commerce_ingestion/idempotency.py
python -m py_compile app/domains/commerce_ingestion/price_bridge.py
python -m py_compile app/domains/commerce_ingestion/runtime.py
python -m py_compile app/api/v1/connector_runtime_router.py

python scripts/check_docker_db_env_consistency.py
python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py
python scripts/api_contract_schema_guard.py
python -m pytest -q
