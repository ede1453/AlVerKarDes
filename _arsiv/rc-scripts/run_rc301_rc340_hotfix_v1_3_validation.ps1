$ErrorActionPreference = "Stop"

python -m pytest `
tests/test_rc340_asyncpg_env_contract.py `
tests/test_rc340_isolated_port_contract.py `
tests/test_rc340_fail_fast_script_contract.py `
tests/test_rc340_smoke_isolation_contract.py -q

python -m py_compile scripts/check_production_env.py
python -m py_compile scripts/production_smoke_test.py

python scripts/check_release_artifacts.py
python scripts/check_docker_db_env_consistency.py
python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py
python scripts/api_contract_schema_guard.py
python -m pytest -q
