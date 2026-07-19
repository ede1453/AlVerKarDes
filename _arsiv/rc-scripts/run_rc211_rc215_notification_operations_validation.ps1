$ErrorActionPreference = "Stop"

python -m pytest `
tests/test_rc211_delivery_attempts.py `
tests/test_rc212_notification_idempotency.py `
tests/test_rc213_notification_escalation.py `
tests/test_rc214_notification_digest.py `
tests/test_rc215_notification_engagement.py `
tests/test_rc211_rc215_notification_operations_api.py `
tests/test_rc211_rc215_notification_operations_openapi.py -q

python -m py_compile app/domains/deal_notifications/operations.py
python -m py_compile app/api/v1/deal_notification_operations_router.py

python scripts/check_docker_db_env_consistency.py
python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py
python scripts/api_contract_schema_guard.py
python -m pytest -q
