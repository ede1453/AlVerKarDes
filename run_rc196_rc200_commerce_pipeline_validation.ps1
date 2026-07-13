$ErrorActionPreference = "Stop"

python -m pytest `
tests/test_rc196_marketplace_normalization_stage.py `
tests/test_rc197_price_quality_stage.py `
tests/test_rc198_deal_decision_stage.py `
tests/test_rc199_pipeline_persistence_stage.py `
tests/test_rc200_end_to_end_commerce_pipeline.py `
tests/test_rc196_rc200_commerce_pipeline_api.py `
tests/test_rc196_rc200_commerce_pipeline_openapi.py -q

python -m py_compile app/domains/commerce_pipeline/service.py
python -m py_compile app/api/v1/commerce_pipeline_router.py

python scripts/check_docker_db_env_consistency.py
python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py
python scripts/api_contract_schema_guard.py
python -m pytest -q
