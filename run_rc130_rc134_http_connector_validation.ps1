$ErrorActionPreference = "Stop"

python -m pytest `
tests/test_rc130_http_connector_execution.py `
tests/test_rc131_robots_rate_limit_policy.py `
tests/test_rc132_http_response_cache.py `
tests/test_rc133_connector_error_classification.py `
tests/test_rc134_connector_sla_metrics.py `
tests/test_rc130_rc134_http_connector_api.py `
tests/test_rc130_rc134_http_connector_openapi.py -q

python -m py_compile app/domains/commerce_ingestion/http_execution.py
python -m py_compile app/api/v1/http_connector_router.py

python scripts/check_docker_db_env_consistency.py
python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py
python scripts/api_contract_schema_guard.py
python -m pytest -q
