$ErrorActionPreference = "Stop"

python -m pytest `
tests/test_rc110_commerce_persistence_repository.py `
tests/test_rc111_import_job_history.py `
tests/test_rc112_feed_adapters.py `
tests/test_rc113_feed_execution_service.py `
tests/test_rc114_quarantine_replay.py `
tests/test_rc110_rc114_execution_api.py `
tests/test_rc110_rc114_execution_openapi.py `
tests/test_rc110_rc114_migration_contract.py `
tests/test_rc171_alembic_linear_history.py -q

python -m py_compile app/domains/commerce_ingestion/persistence.py
python -m py_compile app/domains/commerce_ingestion/adapters.py
python -m py_compile app/domains/commerce_ingestion/execution.py
python -m py_compile app/api/v1/commerce_ingestion_execution_router.py

python scripts/check_docker_db_env_consistency.py
python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py
python scripts/api_contract_schema_guard.py
python -m pytest -q
