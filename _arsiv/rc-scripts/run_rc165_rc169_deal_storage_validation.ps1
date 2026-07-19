$ErrorActionPreference = "Stop"

python -m pytest `
tests/test_rc165_deal_storage_repository.py `
tests/test_rc166_transactional_outbox.py `
tests/test_rc167_retention_purge.py `
tests/test_rc168_integrity_audit.py `
tests/test_rc169_backup_manifest.py `
tests/test_rc165_rc169_deal_storage_api.py `
tests/test_rc165_rc169_deal_storage_openapi.py -q

python -m py_compile app/domains/deal_storage/service.py
python -m py_compile app/api/v1/deal_storage_router.py

python scripts/check_docker_db_env_consistency.py
python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py
python scripts/api_contract_schema_guard.py
python -m pytest -q
