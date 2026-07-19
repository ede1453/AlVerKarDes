$ErrorActionPreference = "Stop"

python -m pytest `
tests/test_rc186_storage_worker_lease.py `
tests/test_rc187_backup_retention_policy.py `
tests/test_rc188_restore_approval_gate.py `
tests/test_rc189_disaster_recovery_plan.py `
tests/test_rc190_storage_slo.py `
tests/test_rc186_rc190_storage_reliability_api.py `
tests/test_rc186_rc190_storage_reliability_openapi.py -q

python -m py_compile app/domains/deal_storage/reliability_governance.py
python -m py_compile app/api/v1/storage_reliability_router.py

python scripts/check_docker_db_env_consistency.py
python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py
python scripts/api_contract_schema_guard.py
python -m pytest -q
