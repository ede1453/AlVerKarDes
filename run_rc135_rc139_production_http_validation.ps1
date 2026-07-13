$ErrorActionPreference = "Stop"

python -m pytest `
tests/test_rc135_production_http_transport.py `
tests/test_rc136_conditional_requests.py `
tests/test_rc137_response_content_validation.py `
tests/test_rc138_pagination_service.py `
tests/test_rc139_multi_page_runtime.py `
tests/test_rc135_rc139_production_http_api.py `
tests/test_rc135_rc139_production_http_openapi.py -q

python -m py_compile app/domains/commerce_ingestion/production_http.py
python -m py_compile app/api/v1/production_http_router.py

python scripts/check_docker_db_env_consistency.py
python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py
python scripts/api_contract_schema_guard.py
python -m pytest -q
