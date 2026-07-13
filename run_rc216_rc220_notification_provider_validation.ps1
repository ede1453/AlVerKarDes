$ErrorActionPreference = "Stop"

python -m pytest `
tests/test_rc216_notification_provider_registry.py `
tests/test_rc217_notification_delivery_policy.py `
tests/test_rc218_notification_subscription_compliance.py `
tests/test_rc219_notification_experiment.py `
tests/test_rc220_notification_performance.py `
tests/test_rc216_rc220_notification_provider_api.py `
tests/test_rc216_rc220_notification_provider_openapi.py -q

python -m py_compile app/domains/deal_notifications/provider_governance.py
python -m py_compile app/api/v1/deal_notification_provider_router.py

python scripts/check_docker_db_env_consistency.py
python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py
python scripts/api_contract_schema_guard.py
python -m pytest -q
