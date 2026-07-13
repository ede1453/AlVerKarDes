$ErrorActionPreference = "Stop"

python -m pytest `
tests/test_rc150_opportunity_repository.py `
tests/test_rc151_decision_history.py `
tests/test_rc152_recommendation_explanation.py `
tests/test_rc153_alert_watchlist_bridge.py `
tests/test_rc154_end_to_end_deal_operations.py `
tests/test_rc150_rc154_deal_operations_api.py `
tests/test_rc150_rc154_deal_operations_openapi.py -q

python -m py_compile app/domains/deal_operations/service.py
python -m py_compile app/api/v1/deal_operations_router.py

python scripts/check_docker_db_env_consistency.py
python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py
python scripts/api_contract_schema_guard.py
python -m pytest -q
