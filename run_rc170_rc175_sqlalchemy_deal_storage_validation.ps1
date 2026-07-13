$ErrorActionPreference = "Stop"

python -m pytest `
tests/test_rc170_sqlalchemy_deal_repository.py `
tests/test_rc172_sqlalchemy_transactional_outbox.py `
tests/test_rc173_sqlalchemy_retention.py `
tests/test_rc174_sqlalchemy_integrity_audit.py `
tests/test_rc175_sqlalchemy_backup_manifest.py `
tests/test_rc170_rc175_sqlalchemy_models_contract.py `
tests/test_rc170_rc175_sqlalchemy_openapi.py `
tests/test_rc170_rc175_migration_contract.py `
tests/test_rc171_alembic_linear_history.py -q

python -m py_compile app/domains/deal_storage/sqlalchemy_models.py
python -m py_compile app/domains/deal_storage/sqlalchemy_repository.py
python -m py_compile app/api/v1/deal_storage_sqlalchemy_router.py

python scripts/check_docker_db_env_consistency.py
python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py
python scripts/api_contract_schema_guard.py
python -m pytest -q
