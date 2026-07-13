$ErrorActionPreference = "Stop"

python -m pytest `
tests/test_rc181_storage_outbox_worker.py `
tests/test_rc182_backup_scheduler.py `
tests/test_rc183_restore_drill.py `
tests/test_rc184_storage_health_dashboard.py `
tests/test_rc185_storage_notification_bridge.py `
tests/test_rc181_rc185_storage_operations_api.py `
tests/test_rc181_rc185_storage_operations_openapi.py -q

python -m py_compile app/domains/deal_storage/operations_runtime.py
python -m py_compile app/api/v1/deal_storage_operations_router.py

python scripts/check_docker_db_env_consistency.py
python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py
python scripts/api_contract_schema_guard.py
python -m pytest -q
