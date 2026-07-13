$ErrorActionPreference = "Stop"

python -m pytest `
tests/test_rc145_price_history_analysis.py `
tests/test_rc146_discount_truth_engine.py `
tests/test_rc147_deal_confidence.py `
tests/test_rc148_opportunity_ranking.py `
tests/test_rc149_recommendation_bridge.py `
tests/test_rc145_rc149_deal_intelligence_api.py `
tests/test_rc145_rc149_deal_intelligence_openapi.py -q

python -m py_compile app/domains/deal_intelligence/service.py
python -m py_compile app/api/v1/deal_intelligence_router.py

python scripts/check_docker_db_env_consistency.py
python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py
python scripts/api_contract_schema_guard.py
python -m pytest -q
