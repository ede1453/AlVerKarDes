$ErrorActionPreference = "Stop"

python -m pytest `
tests/test_rc176_outbox_publisher.py `
tests/test_rc177_outbox_retry_dead_letter.py `
tests/test_rc178_backup_export.py `
tests/test_rc179_restore_validation.py `
tests/test_rc180_storage_health.py `
tests/test_rc176_rc180_resilience_api.py `
tests/test_rc176_rc180_resilience_openapi.py -q

python -m py_compile app/domains/deal_storage/resilience.py
python -m py_compile app/api/v1/deal_storage_resilience_router.py

python scripts/check_docker_db_env_consistency.py
python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py
python scripts/api_contract_schema_guard.py
python -m pytest -q
