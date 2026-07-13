$ErrorActionPreference = "Stop"

python -m pytest `
tests/test_rc221_notification_fatigue.py `
tests/test_rc222_frequency_cap.py `
tests/test_rc223_provider_health.py `
tests/test_rc224_provider_fallback.py `
tests/test_rc225_delivery_sla.py `
tests/test_rc226_feedback_capture.py `
tests/test_rc227_acceptance_metrics.py `
tests/test_rc228_false_positive.py `
tests/test_rc229_source_trust_adjustment.py `
tests/test_rc230_feedback_analytics.py `
tests/test_rc231_budget_policy.py `
tests/test_rc232_category_quota.py `
tests/test_rc233_saved_search.py `
tests/test_rc234_deal_comparison.py `
tests/test_rc235_purchase_intent.py `
tests/test_rc236_conversion_attribution.py `
tests/test_rc237_affiliate_disclosure.py `
tests/test_rc238_sponsored_separation.py `
tests/test_rc239_recommendation_audit.py `
tests/test_rc240_consumer_trust_dashboard.py `
tests/test_rc221_rc240_consumer_trust_api.py `
tests/test_rc221_rc240_consumer_trust_openapi.py -q

python -m py_compile app/domains/consumer_trust/service.py
python -m py_compile app/api/v1/consumer_trust_router.py

python scripts/check_docker_db_env_consistency.py
python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py
python scripts/api_contract_schema_guard.py
python -m pytest -q
