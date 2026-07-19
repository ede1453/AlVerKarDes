$ErrorActionPreference = "Stop"

python -m pytest `
tests/test_rc206_deal_alert_eligibility.py `
tests/test_rc207_notification_preferences.py `
tests/test_rc208_deal_quiet_hours.py `
tests/test_rc209_notification_channel_routing.py `
tests/test_rc210_deal_notification_service.py `
tests/test_rc206_rc210_deal_notifications_api.py `
tests/test_rc206_rc210_deal_notifications_openapi.py -q

python -m py_compile app/domains/deal_notifications/service.py
python -m py_compile app/api/v1/deal_notifications_router.py

python scripts/check_docker_db_env_consistency.py
python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py
python scripts/api_contract_schema_guard.py
python -m pytest -q
