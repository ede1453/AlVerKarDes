$ErrorActionPreference = "Stop"

python -m pytest `
tests/test_rc191_storage_capacity_planning.py `
tests/test_rc192_storage_encryption_policy.py `
tests/test_rc193_storage_access_audit.py `
tests/test_rc194_storage_maintenance_window.py `
tests/test_rc195_storage_production_readiness.py `
tests/test_rc191_rc195_storage_readiness_api.py `
tests/test_rc191_rc195_storage_readiness_openapi.py -q

python -m py_compile app/domains/deal_storage/production_readiness.py
python -m py_compile app/api/v1/storage_production_readiness_router.py

python scripts/check_docker_db_env_consistency.py
python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py
python scripts/api_contract_schema_guard.py
python -m pytest -q
