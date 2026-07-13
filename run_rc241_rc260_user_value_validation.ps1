$ErrorActionPreference = "Stop"

python -m pytest `
tests/test_rc241_savings_calculation.py `
tests/test_rc242_savings_event.py `
tests/test_rc243_lifetime_savings.py `
tests/test_rc244_price_trend.py `
tests/test_rc245_purchase_timing.py `
tests/test_rc246_target_price.py `
tests/test_rc247_alternative_products.py `
tests/test_rc248_price_alert.py `
tests/test_rc249_watch_entry.py `
tests/test_rc250_watch_expiry.py `
tests/test_rc251_decision_explanation.py `
tests/test_rc252_decision_consistency.py `
tests/test_rc253_journey_event.py `
tests/test_rc254_funnel_metrics.py `
tests/test_rc255_recommendation_value.py `
tests/test_rc256_churn_risk.py `
tests/test_rc257_retention_action.py `
tests/test_rc258_purchase_record.py `
tests/test_rc259_repeat_purchase_guard.py `
tests/test_rc260_user_value_dashboard.py `
tests/test_rc241_rc260_user_value_api.py `
tests/test_rc241_rc260_user_value_openapi.py -q

python -m py_compile app/domains/user_value/service.py
python -m py_compile app/api/v1/user_value_router.py

python scripts/check_docker_db_env_consistency.py
python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py
python scripts/api_contract_schema_guard.py
python -m pytest -q
