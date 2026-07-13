$ErrorActionPreference = "Stop"

python -m pytest `
tests/test_rc201_cross_market_product_identity.py `
tests/test_rc202_offer_deduplication.py `
tests/test_rc203_user_preference_scoring.py `
tests/test_rc204_personalized_deal_feed.py `
tests/test_rc205_deal_feed_service.py `
tests/test_rc201_rc205_deal_feed_api.py `
tests/test_rc201_rc205_deal_feed_openapi.py -q

python -m py_compile app/domains/deal_feed/service.py
python -m py_compile app/api/v1/deal_feed_router.py

python scripts/check_docker_db_env_consistency.py
python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py
python scripts/api_contract_schema_guard.py
python -m pytest -q
