$ErrorActionPreference = "Stop"

python -m pytest `
tests/test_rc155_deal_idempotency.py `
tests/test_rc156_decision_versioning.py `
tests/test_rc157_watch_policy.py `
tests/test_rc158_deal_lifecycle.py `
tests/test_rc159_deal_queries_events.py `
tests/test_rc155_rc159_deal_lifecycle_api.py `
tests/test_rc155_rc159_deal_lifecycle_openapi.py -q

python -m py_compile app/domains/deal_lifecycle/service.py
python -m py_compile app/api/v1/deal_lifecycle_router.py

python scripts/check_docker_db_env_consistency.py
python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py
python scripts/api_contract_schema_guard.py
python -m pytest -q
