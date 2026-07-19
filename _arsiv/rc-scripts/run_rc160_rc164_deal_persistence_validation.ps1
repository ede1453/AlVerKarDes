$ErrorActionPreference = "Stop"

python -m pytest `
tests/test_rc160_deal_persistence.py `
tests/test_rc161_deal_snapshot.py `
tests/test_rc162_deal_checkpoint.py `
tests/test_rc163_deal_archive.py `
tests/test_rc164_deal_recovery.py `
tests/test_rc160_rc164_deal_persistence_api.py `
tests/test_rc160_rc164_deal_persistence_openapi.py `
tests/test_rc160_rc164_migration_contract.py `
tests/test_rc171_alembic_linear_history.py -q

python -m py_compile app/domains/deal_persistence/service.py
python -m py_compile app/api/v1/deal_persistence_router.py

python scripts/check_docker_db_env_consistency.py
python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py
python scripts/api_contract_schema_guard.py
python -m pytest -q
